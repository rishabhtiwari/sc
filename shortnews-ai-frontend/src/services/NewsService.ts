import axios from "axios";
import { Article } from "../models/Article";

// API Server Configuration (correct architecture)
// Use localhost for web/browser, host IP for mobile devices
const isWeb = typeof window !== 'undefined';
const getApiUrl = () => {
  if (process.env.API_BASE_URL) {
    return process.env.API_BASE_URL;
  }

  if (isWeb) {
    return "http://localhost:8080";
  }

  // For mobile devices, use the host machine's IP address
  // This is your computer's IP address on the local network
  return "http://192.168.29.163:8080";
};

const API_SERVER_URL = getApiUrl();
const DEFAULT_PAGE_SIZE = 10; // Fetch top 10 latest news as requested

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
    console.log("🔄 NewsService: Starting fetchTopHeadlines...");
    console.log("📋 NewsService: Request parameters:", { page, category, q });
    console.log("🌐 NewsService: API Server URL:", API_SERVER_URL);

    try {
      // Build query parameters for api-server news endpoint
      const params: Record<string, string | number | undefined> = {
        page,
        page_size: DEFAULT_PAGE_SIZE,
        category: category || "general",
        language: "en",
        country: "in", // Default to India as per config
      };

      console.log("📤 NewsService: Sending request with params:", params);
      console.log("🔗 NewsService: Full URL:", `${API_SERVER_URL}/api/news`);

      // Call api-server news endpoint (which will call job-news-fetcher internally)
      const res = await axios.get(`${API_SERVER_URL}/api/news`, {
        params,
        timeout: 10000, // 10 second timeout
      });

      console.log("✅ NewsService: API Response received");
      console.log("📊 NewsService: Response status:", res.status);
      console.log("📄 NewsService: Response data keys:", Object.keys(res.data || {}));
      console.log("🔍 NewsService: Full response data:", JSON.stringify(res.data, null, 2));

      if (res.data.status === 'error') {
        console.error("❌ NewsService: API returned error status:", res.data.error);
        throw new Error(res.data.error || 'Failed to fetch news');
      }

      // Extract articles from the api-server response (which wraps news-fetcher data)
      let articles: Article[] = res.data.articles || [];
      console.log("📰 NewsService: Raw articles count:", articles.length);
      console.log("📝 NewsService: First article sample:", articles[0] ? JSON.stringify(articles[0], null, 2) : "No articles");

      // If there's a search query, filter articles on the frontend
      if (q && q.trim()) {
        console.log("🔍 NewsService: Applying search filter for:", q);
        const searchTerm = q.toLowerCase().trim();
        const originalCount = articles.length;
        articles = articles.filter((article: any) =>
          article.title?.toLowerCase().includes(searchTerm) ||
          article.description?.toLowerCase().includes(searchTerm) ||
          article.content?.toLowerCase().includes(searchTerm)
        );
        console.log(`🔍 NewsService: Search filtered ${originalCount} -> ${articles.length} articles`);
      }

      // Map the news-fetcher API response to our Article interface
      console.log("🔄 NewsService: Mapping articles to interface...");
      const mappedArticles: Article[] = articles.map((a: any, index: number) => {
        const mapped = {
          id: a._id || a.id || a.url, // Use MongoDB _id or fallback to URL
          title: a.title || "No Title",
          description: a.description || a.summary || "",
          content: a.content || a.short_summary || "",
          url: a.url || a.link || "",
          image: a.image || a.image_url || a.imageUrl || "",
          source: (typeof a.source === 'object' && a.source?.name) ? a.source.name : (a.source || "Unknown Source"),
          publishedAt: a.published_at || a.publishedAt || new Date().toISOString(),
          category: a.category || category,
        };

        if (index === 0) {
          console.log("📝 NewsService: First mapped article:", JSON.stringify(mapped, null, 2));
        }

        return mapped;
      });

      // Calculate total results from pagination info
      const totalResults = res.data.pagination?.total_articles || mappedArticles.length;
      console.log("📊 NewsService: Final results:", {
        articlesCount: mappedArticles.length,
        totalResults,
        pagination: res.data.pagination
      });

      console.log("✅ NewsService: Successfully returning data");
      return {
        articles: mappedArticles,
        totalResults
      };

    } catch (err: any) {
      console.error("❌ NewsService: Error occurred!");
      console.error("❌ NewsService: Error type:", err.constructor.name);
      console.error("❌ NewsService: Error message:", err.message);
      console.error("❌ NewsService: Error code:", err.code);
      console.error("❌ NewsService: Error response:", err.response?.data);
      console.error("❌ NewsService: Error status:", err.response?.status);
      console.error("❌ NewsService: Full error:", err);

      // Provide fallback empty response instead of throwing
      console.log("🔄 NewsService: Returning empty fallback response");
      return {
        articles: [],
        totalResults: 0
      };
    }
  }
}
