import apiClient from './apiClient';

// Types for fortune API responses
interface FortuneApiResponse {
  deity_id: string;
  deity_name: string;
  number: number;
  poem: {
    id: string;
    temple: string;
    title: string;
    fortune: string;
    poem: string;
    analysis: string | { [key: string]: string };
  };
  temple_source: string;
}

interface DailyFortuneApiResponse {
  date: string;
  deity_id: string;
  deity_name: string;
  number: number;
  poem: {
    id: string;
    title: string;
    fortune: string;
    poem: string;
    analysis: string;
  };
  message: string;
}

// Transform backend API data to frontend format - preserve multilingual analysis
const transformFortuneData = (apiResponse: FortuneApiResponse) => {
  return {
    deity_id: apiResponse.deity_id,
    deity_name: apiResponse.deity_name,
    number: apiResponse.number,
    poem: {
      id: apiResponse.poem.id,
      temple: apiResponse.poem.temple,
      title: apiResponse.poem.title,
      fortune: apiResponse.poem.fortune,
      poem: apiResponse.poem.poem,
      analysis: apiResponse.poem.analysis // Preserve original multilingual structure
    },
    temple_source: apiResponse.temple_source
  };
};

// Map backend fortune levels to frontend display
const mapFortuneLevel = (backendFortune: string): string => {
  const fortuneMap: { [key: string]: string } = {
    'great_fortune': 'Great Fortune',
    'good_fortune': 'Good Fortune',
    'medium_fortune': 'Medium Fortune',
    'neutral': 'Neutral',
    'bad_fortune': 'Caution',
    'great_bad': 'Great Caution',
    // Handle Chinese fortune levels
    '大吉': 'Great Fortune',
    '中吉': 'Good Fortune',
    '小吉': 'Medium Fortune',
    '吉': 'Good Fortune',
    '平': 'Neutral',
    '凶': 'Caution'
  };
  
  return fortuneMap[backendFortune] || backendFortune || 'Unknown';
};

class FortuneService {
  // Fetch specific fortune by deity ID and number
  async getFortuneByDeityAndNumber(deityId: string, number: number) {
    try {
      const response: FortuneApiResponse = await apiClient.get(`/api/v1/fortune/fortunes/${deityId}/${number}`);
      return transformFortuneData(response);
    } catch (error: any) {
      console.error(`Error fetching fortune for ${deityId} #${number}:`, error);
      
      // Return mock data if API fails (for development)
      if (error.response?.status === 404) {
        return this.getMockFortune(deityId, number);
      }
      
      throw error;
    }
  }

  // Fetch daily fortune (free endpoint)
  async getDailyFortune() {
    try {
      const response: DailyFortuneApiResponse = await apiClient.get('/api/v1/fortune/daily');
      
      return {
        id: response.poem.id,
        title: response.poem.title,
        poem: response.poem.poem,
        fortuneLevel: mapFortuneLevel(response.poem.fortune),
        analysis: response.poem.analysis,
        deity: {
          id: response.deity_id,
          name: response.deity_name
        },
        number: response.number,
        date: response.date,
        message: response.message
      };
    } catch (error) {
      console.error('Error fetching daily fortune:', error);
      
      // Return mock daily fortune if API fails
      return {
        id: 'daily_mock',
        title: 'Daily Guidance',
        poem: 'The path of wisdom unfolds with each step taken mindfully.',
        fortuneLevel: 'Good Fortune',
        analysis: 'Today brings opportunities for growth and reflection. Trust in your inner guidance.',
        deity: {
          id: 'guan_yin',
          name: 'Guan Yin'
        },
        number: 1,
        date: new Date().toISOString().split('T')[0],
        message: 'Today\'s guidance from the divine'
      };
    }
  }

  // Search poems (free endpoint)
  async searchPoems(query: string, temple?: string, limit: number = 10) {
    try {
      const params: any = { q: query, limit };
      if (temple) {
        params.temple = temple;
      }
      
      const response = await apiClient.get('/api/v1/fortune/search', { params });
      return response;
    } catch (error) {
      console.error('Error searching poems:', error);
      return { query, results: [], total_found: 0, search_time_ms: 0 };
    }
  }

  // Get fortune categories (free endpoint)
  async getFortuneCategories() {
    try {
      const response = await apiClient.get('/api/v1/fortune/categories');
      return response;
    } catch (error) {
      console.error('Error fetching fortune categories:', error);
      return {
        categories: ['great_fortune', 'good_fortune', 'neutral', 'bad_fortune'],
        category_counts: {
          great_fortune: 0,
          good_fortune: 0,
          neutral: 0,
          bad_fortune: 0
        }
      };
    }
  }

  // Mock fortune data for development/fallback
  private getMockFortune(deityId: string, number: number) {
    const mockPoems = {
      'guan_yin_7': {
        id: `${deityId}_${number}`,
        title: '第七籤 · 天賜良緣',
        poem: '天賜良緣自有期\n不須過慮費心思\n只要心存仁義德\n自有福神暗佑之',
        fortuneLevel: 'Good Fortune',
        analysis: 'This fortune speaks of divine timing and natural flow. The heavens have already arranged what is meant to be, so there is no need for excessive worry or forced effort. By maintaining righteousness and virtue in your heart, you will receive protection and blessings from benevolent spirits. Trust in the process and let things unfold naturally.',
        deity: {
          id: deityId,
          name: deityId === 'guan_yin' ? 'Guan Yin' : 'Divine Guide'
        },
        number: number,
        temple: 'Mock Temple'
      }
    };

    const key = `${deityId}_${number}` as keyof typeof mockPoems;
    return mockPoems[key] || mockPoems['guan_yin_7'];
  }
}

// Create singleton instance
const fortuneService = new FortuneService();
export default fortuneService;