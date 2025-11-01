export interface Article {
  id: string;
  title: string;
  description?: string;
  content?: string;
  url: string;
  imageUrl?: string;
  source: string;
  publishedAt: string;
  category?: string;
}
