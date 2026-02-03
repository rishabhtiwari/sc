"""
Project Routes
Proxy routes for design editor project management
"""
from flask import Blueprint, request, jsonify, Response
import requests
import logging
from middleware.jwt_middleware import get_request_headers_with_context

logger = logging.getLogger(__name__)

project_bp = Blueprint('project', __name__)

ASSET_SERVICE_URL = 'http://ichat-asset-service:8099'


@project_bp.route('/projects/', methods=['POST'])
def create_project():
    """Proxy: Create project"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        
        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/projects/',
            headers=headers,
            json=request.get_json(),
            timeout=30
        )
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Proxy: Get project"""
    try:
        headers = get_request_headers_with_context()
        
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/projects/{project_id}',
            headers=headers,
            timeout=30
        )
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Proxy: Update project"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        
        response = requests.put(
            f'{ASSET_SERVICE_URL}/api/projects/{project_id}',
            headers=headers,
            json=request.get_json(),
            timeout=30
        )
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/projects/', methods=['GET'])
def list_projects():
    """Proxy: List projects"""
    try:
        headers = get_request_headers_with_context()
        
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/projects/',
            headers=headers,
            params=request.args,
            timeout=30
        )
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Proxy: Delete project"""
    try:
        headers = get_request_headers_with_context()
        
        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/projects/{project_id}',
            headers=headers,
            params=request.args,
            timeout=30
        )
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ========== Export Routes ==========

@project_bp.route('/projects/export', methods=['POST'])
def create_export():
    """Proxy: Create export job"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/projects/export',
            headers=headers,
            json=request.get_json(),
            timeout=60  # Longer timeout for export creation
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error creating export: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/projects/export/<export_job_id>/status', methods=['GET'])
def get_export_status(export_job_id):
    """Proxy: Get export job status"""
    try:
        headers = get_request_headers_with_context()

        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/projects/export/{export_job_id}/status',
            headers=headers,
            timeout=30
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/projects/export/<export_job_id>', methods=['DELETE'])
def cancel_export(export_job_id):
    """Proxy: Cancel export job"""
    try:
        headers = get_request_headers_with_context()

        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/projects/export/{export_job_id}',
            headers=headers,
            timeout=30
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error cancelling export: {str(e)}")
        return jsonify({'error': str(e)}), 500

