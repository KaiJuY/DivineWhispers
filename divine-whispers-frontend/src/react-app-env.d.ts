/// <reference types="react-scripts" />

// Allow importing JSON files
declare module "*.json" {
  const value: any;
  export default value;
}
