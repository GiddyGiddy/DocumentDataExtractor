export const getFileSizeInMB = (size: number) =>
  `${(size / 1024 / 1024).toFixed(2)} MB`;
