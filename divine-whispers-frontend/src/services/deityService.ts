import apiClient from './apiClient';

// Types for backend API responses
interface NumberRange {
  start: number;
  end: number;
}

interface FortuneNumber {
  number: number;
  is_available: boolean;
  fortune_category: string | null;
  title: string | null;
}

interface Collection {
  id: string;
  name: string;
  description: string;
  number_range: NumberRange;
  temple_mapping: string;
}

interface DeityApiResponse {
  id: string;
  name: string;
  chinese_name: string;
  description: string[];
  collections: Collection[];
  total_fortunes: number;
  deity_image_url: string | null;
}

interface DeitiesListApiResponse {
  deities: DeityApiResponse[];
  total_count: number;
}

// Transform backend API data to frontend format
const transformDeityData = (apiDeity: DeityApiResponse) => {
  return {
    id: apiDeity.id,
    name: apiDeity.name,
    chinese_name: apiDeity.chinese_name,
    description: apiDeity.description, // Use actual description array from API
    templateMapping: (apiDeity.collections && apiDeity.collections.length > 0) ? apiDeity.collections[0].temple_mapping : apiDeity.id,
    imageUrl: apiDeity.deity_image_url || `/assets/${apiDeity.name}.jpg`, // Fallback to asset path
    isActive: true,
    totalPoems: apiDeity.total_fortunes,
    collections: (apiDeity.collections || []).map(collection => ({
      id: collection.id,
      name: collection.name,
      description: collection.description,
      maxNumber: collection.number_range.end,
      templateMapping: collection.temple_mapping,
      numberRange: collection.number_range
    }))
  };
};

class DeityService {
  // Fetch all deities from backend
  async getDeities() {
    try {
      const response: DeitiesListApiResponse = await apiClient.get('/api/v1/deities');
      
      // Transform backend data to frontend format
      const deities = response.deities.map(transformDeityData);
      
      return deities;
    } catch (error) {
      console.error('Error fetching deities:', error);
      // Fallback to empty array if API fails
      return [];
    }
  }

  // Fetch specific deity details
  async getDeityById(deityId: string) {
    try {
      const response = await apiClient.get(`/api/v1/deities/${deityId}`);
      return transformDeityData(response.deity);
    } catch (error) {
      console.error(`Error fetching deity ${deityId}:`, error);
      return null;
    }
  }

  // Fetch available fortune collections for a deity
  async getDeityCollections(deityId: string) {
    try {
      const response = await apiClient.get(`/api/v1/deities/${deityId}/collections`);
      return {
        deityId: response.deity_id,
        deityName: response.deity_name,
        collections: response.collections.map((collection: Collection) => ({
          id: collection.id,
          name: collection.name,
          description: collection.description,
          maxNumber: collection.number_range.end,
          templateMapping: collection.temple_mapping,
          numberRange: collection.number_range
        }))
      };
    } catch (error) {
      console.error(`Error fetching collections for deity ${deityId}:`, error);
      return null;
    }
  }

}

// Create singleton instance
const deityService = new DeityService();
export default deityService;