import React from "react";
import { Image, Text, TouchableOpacity, View, StyleSheet } from "react-native";
import { Article } from "../../models/Article";

interface Props {
  article: Article;
  onPress: () => void;
}

export default function ArticleCard({ article, onPress }: Props) {
  return (
    <TouchableOpacity onPress={onPress} style={styles.card}>
      {article.image && (
        <Image
          source={{ uri: article.image }}
          style={styles.image}
          resizeMode="cover"
        />
      )}
      <View style={styles.content}>
        <Text numberOfLines={3} style={styles.title}>
          {article.title}
        </Text>
        {article.description && (
          <Text numberOfLines={4} style={styles.summary}>
            {article.description}
          </Text>
        )}
        <View style={styles.footer}>
          <Text style={styles.source}>{article.source}</Text>
          <Text style={styles.date}>
            {new Date(article.publishedAt).toLocaleDateString()}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 16,
    marginHorizontal: 4,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: 200,
  },
  content: {
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    lineHeight: 24,
    marginBottom: 8,
  },
  summary: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  source: {
    fontSize: 12,
    color: '#888',
    fontWeight: '600',
  },
  date: {
    fontSize: 12,
    color: '#888',
  },
});
