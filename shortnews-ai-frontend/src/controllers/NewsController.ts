import { Article } from "../models/Article";
import NewsService from "../services/NewsService";
import CacheController from "./CacheController";

export default class NewsController {
  static async getArticles({
    page = 1,
    category = "general",
    q = "",
  }: {
    page?: number;
    category?: string;
    q?: string;
  }): Promise<{ articles: Article[]; totalResults: number }> {
    if (page === 1) {
      const cached = await CacheController.getCached(`home_${category}_${q}`);
      if (cached) return cached;
    }
    const { articles, totalResults } = await NewsService.fetchTopHeadlines({
      page,
      category,
      q,
    });
    if (page === 1)
      await CacheController.setCached(`home_${category}_${q}`, {
        articles,
        totalResults,
      });
    return { articles, totalResults };
  }
}
