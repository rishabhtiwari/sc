import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import NewsController from "../../controllers/NewsController";
import { Article } from "../../models/Article";
import ArticleCard from "../components/ArticleCard";

interface HomeProps {
  navigation: any;
  toggleTheme: () => void;
}

export default function Home({ navigation, toggleTheme }: HomeProps) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("general");

  const load = useCallback(
    async (opts: { page: number; refresh?: boolean }) => {
      try {
        if (opts.refresh) setRefreshing(true);
        else setLoading(true);
        const res = await NewsController.getArticles({
          page: opts.page,
          category,
          q: query,
        });
        if (opts.page === 1) setArticles(res.articles);
        else setArticles((prev) => [...prev, ...res.articles]);
        setPage(opts.page);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [category, query]
  );

  useEffect(() => {
    load({ page: 1 });
  }, [category, query]);

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <View
        style={{ flexDirection: "row", alignItems: "center", marginBottom: 8 }}
      >
        <TextInput
          placeholder="Search news..."
          value={query}
          onChangeText={setQuery}
          style={{
            flex: 1,
            borderWidth: 1,
            padding: 8,
            borderRadius: 8,
            marginRight: 8,
          }}
        />
        <TouchableOpacity onPress={toggleTheme} style={{ padding: 8 }}>
          <Text>Theme</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => navigation.navigate("Bookmarks")}
          style={{ padding: 8 }}
        >
          <Text>Bookmarks</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={articles}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ArticleCard
            article={item}
            onPress={() => navigation.navigate("Article", { article: item })}
          />
        )}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load({ page: 1, refresh: true })}
          />
        }
        onEndReached={() => load({ page: page + 1 })}
        onEndReachedThreshold={0.5}
        ListFooterComponent={loading ? <ActivityIndicator /> : null}
      />
    </View>
  );
}
