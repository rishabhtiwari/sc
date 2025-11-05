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
    console.log("🎯 NewsController: getArticles called with:", { page, category, q });

    // if (page === 1) {
    //   console.log("🔍 NewsController: Checking cache for page 1...");
    //   const cached = await CacheController.getCached(`home_${category}_${q}`);
    //   if (cached) {
    //     console.log("✅ NewsController: Cache hit! Returning cached data:", cached.articles.length, "articles");
    //     return cached;
    //   }
    //   console.log("❌ NewsController: Cache miss, fetching from API...");
    // }

    console.log("📡 NewsController: Calling NewsService.fetchTopHeadlines...");
    const { articles, totalResults } = await NewsService.fetchTopHeadlines({
      page,
      category,
      q,
    });

    console.log("📊 NewsController: Received from NewsService:", {
      articlesCount: articles.length,
      totalResults
    });

    // if (page === 1) {
    //   console.log("💾 NewsController: Caching results for page 1...");
    //   await CacheController.setCached(`home_${category}_${q}`, {
    //     articles,
    //     totalResults,
    //   });
    // }

    console.log("✅ NewsController: Returning final results");
    return { articles, totalResults };
  }
}
