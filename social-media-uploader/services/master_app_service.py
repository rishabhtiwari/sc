"""
Master App Service
Manages social media master app credentials (Facebook/Instagram apps)
Provides CRUD operations with encryption for sensitive data
Each customer has their own encryption key stored in database
"""

import logging
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from utils.encryption import encrypt_value, decrypt_value, generate_encryption_key

logger = logging.getLogger(__name__)


class MasterAppService:
    """Service for managing social media master app credentials"""

    def __init__(self, db):
        """
        Initialize MasterAppService

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db['social_media_master_apps']
        self.encryption_keys_collection = db['customer_encryption_keys']

        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create database indexes for performance and uniqueness"""
        try:
            # Index for finding active app for customer+platform
            self.collection.create_index([
                ('customer_id', 1),
                ('platform', 1),
                ('is_active', 1)
            ], name='customer_platform_active_idx')

            # Index for listing customer's apps
            self.collection.create_index([
                ('customer_id', 1)
            ], name='customer_idx')

            # Unique index: only one active app per customer per platform
            self.collection.create_index([
                ('customer_id', 1),
                ('platform', 1),
                ('is_active', 1)
            ], unique=True, partialFilterExpression={'is_active': True}, name='unique_active_app_idx')

            # Index for encryption keys collection
            self.encryption_keys_collection.create_index([
                ('customer_id', 1)
            ], unique=True, name='customer_encryption_key_idx')

            logger.info("✅ Master app indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")

    def _get_or_create_encryption_key(self, customer_id):
        """
        Get or create encryption key for customer

        Args:
            customer_id (str): Customer ID

        Returns:
            str: Encryption key for the customer
        """
        try:
            # Try to get existing key
            key_doc = self.encryption_keys_collection.find_one({'customer_id': customer_id})

            if key_doc:
                return key_doc['encryption_key']

            # Generate new key for customer
            new_key = generate_encryption_key()

            key_document = {
                'customer_id': customer_id,
                'encryption_key': new_key,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            self.encryption_keys_collection.insert_one(key_document)
            logger.info(f"✅ Generated new encryption key for customer={customer_id}")

            return new_key

        except Exception as e:
            logger.error(f"❌ Failed to get/create encryption key: {e}")
            raise

    def create_master_app(self, customer_id, user_id, app_data):
        """
        Create a new master app

        Args:
            customer_id (str): Customer ID
            user_id (str): User ID who is creating the app
            app_data (dict): App configuration
                - platform (str): "instagram", "tiktok", etc.
                - app_name (str): User-friendly name
                - app_id (str): Platform app ID
                - app_secret (str): Platform app secret (will be encrypted)
                - redirect_uri (str): OAuth callback URL
                - scopes (list): Required permissions
                - metadata (dict): Additional metadata

        Returns:
            dict: Created master app document (without decrypted secret)
        """
        try:
            # Validate required fields
            required_fields = ['platform', 'app_name', 'app_id', 'app_secret']
            for field in required_fields:
                if field not in app_data or not app_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # If this is being set as active, deactivate other apps for same platform
            is_active = app_data.get('is_active', True)
            if is_active:
                self._deactivate_platform_apps(customer_id, app_data['platform'])

            # Get or create encryption key for customer
            encryption_key = self._get_or_create_encryption_key(customer_id)

            # Encrypt the app secret using customer's encryption key
            encrypted_secret = encrypt_value(app_data['app_secret'], encryption_key)

            # Prepare document
            now = datetime.utcnow()
            document = {
                'customer_id': customer_id,
                'platform': app_data['platform'],
                'app_name': app_data['app_name'],
                'app_id': app_data['app_id'],
                'app_secret': encrypted_secret,  # Encrypted
                'redirect_uri': app_data.get('redirect_uri', ''),
                'scopes': app_data.get('scopes', []),
                'is_active': is_active,
                'created_by': user_id,
                'created_at': now,
                'updated_at': now,
                'metadata': app_data.get('metadata', {})
            }

            # Insert into database
            result = self.collection.insert_one(document)
            document['_id'] = result.inserted_id

            logger.info(f"✅ Created master app: {app_data['app_name']} for customer {customer_id}")

            # Return without decrypted secret
            return self._sanitize_app_document(document)

        except DuplicateKeyError:
            raise ValueError(f"An active {app_data['platform']} app already exists for this customer")
        except Exception as e:
            logger.error(f"❌ Failed to create master app: {e}")
            raise

    def get_master_app(self, customer_id, app_id, decrypt_secret=False):
        """
        Get a specific master app by ID

        Args:
            customer_id (str): Customer ID
            app_id (str): Master app ID
            decrypt_secret (bool): Whether to decrypt and return the app secret

        Returns:
            dict: Master app document
        """
        try:
            document = self.collection.find_one({
                '_id': ObjectId(app_id),
                'customer_id': customer_id
            })

            if not document:
                return None

            if decrypt_secret:
                # Get customer's encryption key
                encryption_key = self._get_or_create_encryption_key(customer_id)
                # Decrypt the secret for OAuth operations
                document['app_secret'] = decrypt_value(document['app_secret'], encryption_key)
            else:
                # Remove secret from response
                document = self._sanitize_app_document(document)

            return document
        except Exception as e:
            logger.error(f"❌ Failed to get master app: {e}")
            raise

    def update_master_app(self, customer_id, app_id, update_data):
        """
        Update a master app

        Args:
            customer_id (str): Customer ID
            app_id (str): Master app ID
            update_data (dict): Fields to update

        Returns:
            dict: Updated master app document
        """
        try:
            # Get existing app
            existing_app = self.get_master_app(customer_id, app_id)
            if not existing_app:
                raise ValueError("Master app not found")

            # Prepare update document
            update_doc = {'updated_at': datetime.utcnow()}

            # Update allowed fields
            allowed_fields = ['app_name', 'app_id', 'redirect_uri', 'scopes', 'metadata']
            for field in allowed_fields:
                if field in update_data:
                    update_doc[field] = update_data[field]

            # Handle app_secret separately (needs encryption)
            if 'app_secret' in update_data and update_data['app_secret']:
                # Get customer's encryption key
                encryption_key = self._get_or_create_encryption_key(customer_id)
                update_doc['app_secret'] = encrypt_value(update_data['app_secret'], encryption_key)

            # Handle is_active (may need to deactivate others)
            if 'is_active' in update_data:
                new_active_state = update_data['is_active']
                if new_active_state and not existing_app.get('is_active'):
                    # Activating this app - deactivate others
                    self._deactivate_platform_apps(customer_id, existing_app['platform'], exclude_id=app_id)
                update_doc['is_active'] = new_active_state

            # Update in database
            result = self.collection.update_one(
                {'_id': ObjectId(app_id), 'customer_id': customer_id},
                {'$set': update_doc}
            )

            if result.modified_count == 0:
                logger.warning(f"⚠️ No changes made to master app {app_id}")
            else:
                logger.info(f"✅ Updated master app {app_id}")

            # Return updated document
            return self.get_master_app(customer_id, app_id)

        except Exception as e:
            logger.error(f"❌ Failed to update master app: {e}")
            raise

    def delete_master_app(self, customer_id, app_id):
        """
        Delete a master app

        Args:
            customer_id (str): Customer ID
            app_id (str): Master app ID

        Returns:
            dict: Deletion result with affected credentials count
        """
        try:
            # Get the app to find platform
            app = self.get_master_app(customer_id, app_id)
            if not app:
                raise ValueError("Master app not found")

            # Count affected credentials
            credentials_collection = self.db[f"{app['platform']}_credentials"]
            affected_count = credentials_collection.count_documents({
                'customer_id': customer_id,
                'master_app_id': ObjectId(app_id)
            })

            # Delete the master app
            result = self.collection.delete_one({
                '_id': ObjectId(app_id),
                'customer_id': customer_id
            })

            if result.deleted_count == 0:
                raise ValueError("Failed to delete master app")

            logger.info(f"✅ Deleted master app {app_id}, {affected_count} credentials affected")

            return {
                'deleted': True,
                'affected_credentials': affected_count,
                'message': f"Master app deleted. {affected_count} user credentials may need to be reconnected."
            }

        except Exception as e:
            logger.error(f"❌ Failed to delete master app: {e}")
            raise

    def get_active_app_for_platform(self, customer_id, platform, decrypt_secret=False):
        """
        Get the active master app for a specific platform

        Args:
            customer_id (str): Customer ID
            platform (str): Platform name (e.g., "instagram")
            decrypt_secret (bool): Whether to decrypt the app secret

        Returns:
            dict: Active master app or None if not found
        """
        try:
            document = self.collection.find_one({
                'customer_id': customer_id,
                'platform': platform,
                'is_active': True
            })

            if not document:
                return None

            if decrypt_secret:
                # Get customer's encryption key
                encryption_key = self._get_or_create_encryption_key(customer_id)
                # Decrypt the secret for OAuth operations
                document['app_secret'] = decrypt_value(document['app_secret'], encryption_key)
            else:
                # Remove secret from response
                document = self._sanitize_app_document(document)

            return document

        except Exception as e:
            logger.error(f"❌ Failed to get active master app: {e}")
            raise

    def _deactivate_platform_apps(self, customer_id, platform, exclude_id=None):
        """
        Deactivate all apps for a platform (except optionally one)

        Args:
            customer_id (str): Customer ID
            platform (str): Platform name
            exclude_id (str): App ID to exclude from deactivation
        """
        try:
            query = {
                'customer_id': customer_id,
                'platform': platform,
                'is_active': True
            }

            if exclude_id:
                query['_id'] = {'$ne': ObjectId(exclude_id)}

            result = self.collection.update_many(
                query,
                {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
            )

            if result.modified_count > 0:
                logger.info(f"✅ Deactivated {result.modified_count} {platform} apps for customer {customer_id}")

        except Exception as e:
            logger.error(f"❌ Failed to deactivate apps: {e}")
            raise

    def _sanitize_app_document(self, document):
        """
        Remove sensitive data from app document before returning to client

        Args:
            document (dict): Master app document

        Returns:
            dict: Sanitized document
        """
        if not document:
            return None

        # Convert ObjectId to string
        if '_id' in document:
            document['_id'] = str(document['_id'])

        # Remove encrypted secret
        if 'app_secret' in document:
            del document['app_secret']

        return document
        """
        List master apps for a customer

        Args:
            customer_id (str): Customer ID
            platform (str): Filter by platform (optional)
            active_only (bool): Only return active apps

        Returns:
            list: List of master app documents
        """
        try:
            query = {'customer_id': customer_id}

            if platform:
                query['platform'] = platform

            if active_only:
                query['is_active'] = True

            documents = list(self.collection.find(query).sort('created_at', -1))

            # Remove secrets from all documents
            return [self._sanitize_app_document(doc) for doc in documents]

        except Exception as e:
            logger.error(f"❌ Failed to list master apps: {e}")
            raise

