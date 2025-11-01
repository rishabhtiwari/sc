import axios from "axios";
import { Article } from "../models/Article";

const API_KEY = "YOUR_NEWSAPI_KEY";
const PAGE_SIZE = 20;

export default class NewsService {
  static async fetchTopHeadlines({
    page = 1,
    category = "general",
    q = "",
  }: {
    page?: number;
    category?: string;
    q?: string;
  }) {
    try {
      const params: Record<string, string | number | undefined> = {
        apiKey: API_KEY,
        pageSize: PAGE_SIZE,
        page,
        q: q || undefined,
        category: category || undefined,
        country: "us",
      };
      const res = await axios.get("https://newsapi.org/v2/top-headlines", {
        params,
      });
      const articles: Article[] = res.data.articles.map((a: any) => ({
        id: a.url,
        title: a.title,
        description: a.description,
        content: a.content,
        url: a.url,
        imageUrl: a.urlToImage,
        source: a.source.name,
        publishedAt: a.publishedAt,
        category,
      }));
      return { articles, totalResults: res.data.totalResults };
    } catch (err: any) {
      console.warn("NewsService error", err.message);
      throw err;
    }
  }
}
