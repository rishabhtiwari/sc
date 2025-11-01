import AsyncStorage from "@react-native-async-storage/async-storage";
import { Article } from "../models/Article";
const BOOKMARK_KEY = "BOOKMARKS_V1";

export default class BookmarksController {
  static async getAll(): Promise<Article[]> {
    const raw = await AsyncStorage.getItem(BOOKMARK_KEY);
    return raw ? JSON.parse(raw) : [];
  }

  static async add(article: Article) {
    const list = await this.getAll();
    if (!list.find((a) => a.id === article.id)) {
      list.unshift(article);
      await AsyncStorage.setItem(BOOKMARK_KEY, JSON.stringify(list));
    }
    return list;
  }

  static async remove(articleId: string) {
    let list = await this.getAll();
    list = list.filter((a) => a.id !== articleId);
    await AsyncStorage.setItem(BOOKMARK_KEY, JSON.stringify(list));
    return list;
  }

  static async toggle(article: Article) {
    const list = await this.getAll();
    const exists = list.find((a) => a.id === article.id);
    if (exists) return this.remove(article.id);
    return this.add(article);
  }
}
