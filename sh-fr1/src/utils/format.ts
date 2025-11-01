export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateString;
  }
};

/**
 * Truncate text if longer than given limit
 */
export const truncateText = (text: string, maxLength = 100): string => {
  if (!text) return "";
  return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
};

/**
 * Capitalize the first letter of a string
 */
export const capitalize = (str: string): string => {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Format source name (e.g., remove trailing URLs or redundant parts)
 */
export const cleanSourceName = (name: string): string => {
  if (!name) return "";
  return name.replace(/\.com|\.in|https?:\/\//g, "").replace(/\bwww\b\.?/, "");
};

export default {
  formatDate,
  truncateText,
  capitalize,
  cleanSourceName,
};
