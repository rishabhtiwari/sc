export interface Article {
  id: string;
  title: string;
  description?: string;
  content?: string;
  url: string;
  image?: string;
  source: string;
  publishedAt: string;
  category?: string;
}
