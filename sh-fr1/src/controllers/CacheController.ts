import AsyncStorage from "@react-native-async-storage/async-storage";
const TTL_MS = 1000 * 60 * 60;

export default class CacheController {
  static async setCached(key: string, value: any) {
    const payload = { ts: Date.now(), value };
    await AsyncStorage.setItem(`@cache_${key}`, JSON.stringify(payload));
  }

  static async getCached(key: string) {
    const raw = await AsyncStorage.getItem(`@cache_${key}`);
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw);
      if (Date.now() - parsed.ts > TTL_MS) {
        await AsyncStorage.removeItem(`@cache_${key}`);
        return null;
      }
      return parsed.value;
    } catch {
      return null;
    }
  }
}
