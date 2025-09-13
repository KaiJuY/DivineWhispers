import apiClient from './apiClient';

// Types for backend API responses
interface DeityApiResponse {
  id: string;
  name: string;
  chinese_name: string;
  description: string;
  temple_mapping: string;
  available_numbers: number[];
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
    description: [apiDeity.chinese_name], // Split description for frontend display
    templateMapping: apiDeity.temple_mapping,
    imageUrl: apiDeity.deity_image_url || `/assets/${apiDeity.name}.jpg`, // Fallback to asset path
    isActive: true,
    totalPoems: apiDeity.total_fortunes,
    collections: [
      {
        id: `${apiDeity.id}_standard`,
        name: "Standard Collection",
        description: `Traditional ${apiDeity.total_fortunes} fortune poems`,
        maxNumber: apiDeity.total_fortunes,
        templateMapping: apiDeity.temple_mapping
      }
    ]
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

  // Fetch available fortune numbers for a deity
  async getDeityFortuneNumbers(deityId: string) {
    try {
      const response = await apiClient.get(`/api/v1/deities/${deityId}/numbers`);
      return {
        deityId: response.deity_id,
        deityName: response.deity_name,
        numbers: response.numbers.map((num: any) => ({
          number: num.number,
          isAvailable: num.is_available,
          category: num.fortune_category,
          title: num.title
        })),
        totalAvailable: response.total_available
      };
    } catch (error) {
      console.error(`Error fetching fortune numbers for deity ${deityId}:`, error);
      return null;
    }
  }
}

// Create singleton instance
const deityService = new DeityService();
export default deityService;