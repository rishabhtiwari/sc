"use client"; // ✅ Forces client-side rendering (Next.js / SSR)

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import NewsController from "../../controllers/NewsController";
import { Article } from "../../models/Article";

// Get screen dimensions
const getScreenDimensions = () => {
  const { width, height } = Dimensions.get("window");
  if ((width === 0 || height === 0) && typeof window !== "undefined") {
    return { width: window.innerWidth || 1024, height: window.innerHeight || 768 };
  }
  return { width, height };
};

const { width: screenWidth, height: screenHeight } = getScreenDimensions();

export default function Home() {
  console.log("🎯 Home component rendering!");

  // State
  const [articles, setArticles] = useState<Article[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMoreData, setHasMoreData] = useState(true);
  const flatListRef = useRef<FlatList>(null);

  // Fetch articles
  const fetchArticleBatch = useCallback(async (page: number) => {
    try {
      console.log("📡 Fetching batch for page:", page);
      if (page === 1) setLoading(true);
      else setLoadingMore(true);

      const response = await NewsController.getArticles({
        page,
        page_size: 10,
        category: "general",
      });

      const newArticles = response.articles || [];
      console.log("✅ Batch loaded:", newArticles.length, "articles for page", page);

      if (page === 1) {
        setArticles(newArticles);
        setCurrentIndex(0);
      } else {
        setArticles(prev => [...prev, ...newArticles]);
      }

      setCurrentPage(page);
      setHasMoreData(newArticles.length >= 10);
    } catch (error) {
      console.error("❌ Error fetching batch:", error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  // Client-side effect to fetch first batch
  useEffect(() => {
    if (typeof window !== "undefined") {
      console.log("🚀 useEffect triggered client-side");
      fetchArticleBatch(1);
    } else {
      console.log("⚠️ Skipping useEffect — server environment");
    }
  }, [fetchArticleBatch]);

  // Optionally load data when screen focused (React Navigation)
  useFocusEffect(
    useCallback(() => {
      console.log("🟢 Home screen focused — loading data");
      fetchArticleBatch(1);
    }, [fetchArticleBatch])
  );

  // Handle scroll for paging
  const handleScroll = useCallback(
    (event: any) => {
      const index = Math.round(event.nativeEvent.contentOffset.y / screenHeight);

      if (index !== currentIndex && index >= 0 && index < articles.length) {
        setCurrentIndex(index);

        const isNearEnd = index >= articles.length - 2;
        const shouldLoadMore = isNearEnd && hasMoreData && !loadingMore && articles.length > 0;

        if (shouldLoadMore) {
          console.log("🔄 Loading next batch...");
          fetchArticleBatch(currentPage + 1);
        }
      }
    },
    [currentIndex, articles.length, hasMoreData, loadingMore, currentPage, fetchArticleBatch]
  );

  // Refresh handler
  const handleRefresh = useCallback(async () => {
    console.log("🔄 Refreshing articles");
    setRefreshing(true);
    setCurrentIndex(0);
    setCurrentPage(1);
    setHasMoreData(true);

    try {
      await fetchArticleBatch(1);
    } finally {
      setRefreshing(false);
    }
  }, [fetchArticleBatch]);

  // Render article card
  const renderArticleCard = useCallback(
    ({ item, index }: { item: Article; index: number }) => {
      const imageUrl =
        item.image || `https://picsum.photos/800/600?random=${index + Date.now()}`;

      return (
        <View style={styles.articleContainer}>
          {/* Background */}
          <View
            style={[
              styles.backgroundImage,
              {
                // @ts-ignore
                backgroundImage: `url(${imageUrl})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
                backgroundRepeat: "no-repeat",
                backgroundColor: `hsl(${index * 60}, 70%, 50%)`,
              },
            ]}
          />
          {/* Content */}
          <View style={styles.contentOverlay}>
            <View style={styles.articleContent}>
              <Text style={styles.sourceText}>{item.source?.name || "News Source"}</Text>
              <Text style={styles.titleText}>{item.title}</Text>
              <Text style={styles.descriptionText}>{item.description}</Text>
              <Text style={styles.timeText}>
                {new Date(item.publishedAt).toLocaleDateString()}
              </Text>
            </View>
          </View>
          {/* Index */}
          <View style={styles.indexIndicator}>
            <Text style={styles.indexText}>
              {index + 1} / {articles.length}
            </Text>
          </View>
        </View>
      );
    },
    [articles.length]
  );

  if (loading && articles.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#fff" />
        <Text style={styles.loadingText}>Loading news articles...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={articles}
        renderItem={renderArticleCard}
        keyExtractor={(item, index) => `${item.id || index}`}
        pagingEnabled
        showsVerticalScrollIndicator={false}
        onScroll={handleScroll}
        scrollEventThrottle={16}
        snapToInterval={screenHeight}
        snapToAlignment="start"
        decelerationRate="fast"
        bounces
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#fff" />}
        getItemLayout={(data, index) => ({
          length: screenHeight,
          offset: screenHeight * index,
          index,
        })}
        initialNumToRender={2}
        maxToRenderPerBatch={3}
        windowSize={5}
        removeClippedSubviews={false}
        ListFooterComponent={
          loadingMore ? (
            <View style={styles.loadingMoreContainer}>
              <ActivityIndicator size="large" color="#fff" />
              <Text style={styles.loadingMoreText}>Loading more articles...</Text>
            </View>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  articleContainer: { width: screenWidth, height: screenHeight, position: "relative" },
  backgroundImage: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  contentOverlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  articleContent: { flex: 1 },
  sourceText: { color: "#fff", fontSize: 14, fontWeight: "600", marginBottom: 8, opacity: 0.8 },
  titleText: { color: "#fff", fontSize: 24, fontWeight: "bold", marginBottom: 12, lineHeight: 30 },
  descriptionText: { color: "#fff", fontSize: 16, lineHeight: 22, marginBottom: 12, opacity: 0.9 },
  timeText: { color: "#fff", fontSize: 12, opacity: 0.7 },
  indexIndicator: {
    position: "absolute",
    top: 50,
    right: 20,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  indexText: { color: "#fff", fontSize: 12, fontWeight: "600" },
  loadingContainer: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#000" },
  loadingText: { color: "#fff", fontSize: 18, marginTop: 16, textAlign: "center" },
  loadingMoreContainer: { height: 100, justifyContent: "center", alignItems: "center", backgroundColor: "#000" },
  loadingMoreText: { color: "#fff", fontSize: 14, marginTop: 8 },
});
