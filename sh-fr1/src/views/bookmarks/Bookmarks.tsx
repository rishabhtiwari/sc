import React, { useEffect, useState } from "react";
import { FlatList, Text, View } from "react-native";
import BookmarksController from "../../controllers/BookmarksController";
import { Article } from "../../models/Article";
import ArticleCard from "../components/ArticleCard";

interface Props {
  navigation: any;
}

export default function Bookmarks({ navigation }: Props) {
  const [bookmarks, setBookmarks] = useState<Article[]>([]);

  useEffect(() => {
    const unsub = navigation.addListener("focus", async () => {
      const all = await BookmarksController.getAll();
      setBookmarks(all);
    });
    return unsub;
  }, [navigation]);

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <FlatList
        data={bookmarks}
        keyExtractor={(i) => i.id}
        renderItem={({ item }) => (
          <ArticleCard
            article={item}
            onPress={() => navigation.navigate("Article", { article: item })}
          />
        )}
        ListEmptyComponent={<Text>No bookmarks yet</Text>}
      />
    </View>
  );
}
