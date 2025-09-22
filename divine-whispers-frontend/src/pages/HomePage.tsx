import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { breathe, borderBreathe, glowPulse, skewFadeIn, floatUp, colors, gradients, media, cardStyles } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { mockTodaysWhisper, mockDeities, mockDemoReport } from '../utils/mockData';
import { usePagesTranslation } from '../hooks/useTranslation';
import fortuneService from '../services/fortuneService';
import deityService from '../services/deityService';

const HomeContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const HeroSection = styled.section`
  padding: 80px 0;
  text-align: center;
  background: ${gradients.heroSection};
  position: relative;
  overflow: hidden;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;

  ${media.tablet} {
    padding: 60px 0;
  }

  ${media.mobile} {
    padding: 40px 0;
  }
`;

const HeroContent = styled.div`
  max-width: 1400px;
  width: 100%;
  padding: 0 40px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  flex-wrap: wrap;

  ${media.tablet} {
    padding: 0 20px;
    gap: 30px;
  }

  ${media.mobile} {
    gap: 20px;
  }
`;

const HeroText = styled.div`
  width: 100%;
  position: relative;
`;

const HeroImage = styled.img`
  width: 100%;
  max-width: 1440px;
  height: auto;
  display: block;
  margin: 0 auto;
`;

const DemoReportButton = styled.button`
  position: absolute;
  bottom: 30px;
  right: 20px;
  background: rgba(212, 175, 55, 0.1);
  border: 2px solid rgba(212, 175, 55, 0.3);
  color: ${colors.primary};
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(15px);

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    border-color: ${colors.primary};
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(212, 175, 55, 0.3);
  }

  ${media.tablet} {
    bottom: 45px;
    right: 15px;
    padding: 10px 16px;
    font-size: 0.9rem;
  }

  ${media.mobile} {
    bottom: 30px;
    right: 10px;
    padding: 8px 14px;
    font-size: 0.85rem;
  }
`;


const TodaysWhisper = styled.div<{ expanded: boolean }>`
  background: rgba(212, 175, 55, 0.05);
  border: 2px solid rgba(212, 175, 55, 0.2);
  border-radius: 20px;
  padding: 20px 30px;
  text-align: center;
  width: 100%;
  max-width: 1440px;
  backdrop-filter: blur(15px);
  cursor: pointer;
  transition: all 0.4s ease;
  position: relative;
  overflow: hidden;
  animation: ${borderBreathe} 3s ease-in-out infinite;
  margin: 0 auto;

  &:hover {
    background: rgba(212, 175, 55, 0.1);
    border-color: rgba(212, 175, 55, 0.4);
    transform: translateY(-3px);
    box-shadow: 0 15px 40px rgba(212, 175, 55, 0.3);
  }

  ${media.tablet} {
    padding: 18px 25px;
  }

  ${media.mobile} {
    padding: 15px 20px;
  }
`;

const MoonContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
`;

const MoonIcon = styled.div`
  font-size: 48px;
  color: ${colors.primary};
  margin-bottom: 10px;
  animation: ${breathe} 3s ease-in-out infinite;
  filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.6));
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.1) 0%, transparent 70%);
    animation: ${glowPulse} 3s ease-in-out infinite;
    z-index: -1;
  }

  ${media.mobile} {
    font-size: 40px;

    &::before {
      width: 60px;
      height: 60px;
    }
  }
`;

const WhisperTitle = styled.h3`
  color: ${colors.primary};
  margin-bottom: 10px;
  font-size: 40px;
  font-weight: 400;
  letter-spacing: 1px;

  ${media.mobile} {
    font-size: 20px;
  }
`;

const ExpandIcon = styled.span<{ expanded: boolean }>`
  transition: transform 0.3s ease;
  font-size: 14px;
  transform: ${props => props.expanded ? 'rotate(180deg)' : 'rotate(0deg)'};
`;

const WhisperCollapsed = styled.div<{ expanded: boolean }>`
  opacity: ${props => props.expanded ? 0 : 0.9};
  font-size: 14px;
  margin-bottom: 0;
  display: ${props => props.expanded ? 'none' : 'block'};
`;

const WhisperExpanded = styled.div<{ expanded: boolean }>`
  max-height: ${props => props.expanded ? '500px' : '0'};
  overflow: hidden;
  transition: all 0.4s ease;
  opacity: ${props => props.expanded ? 1 : 0};
  margin-top: ${props => props.expanded ? '20px' : '0'};
`;

const WhisperPoem = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(212, 175, 55, 0.2);

  ${media.mobile} {
    padding: 15px;
  }
`;

const PoemChinese = styled.div`
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 15px;
  color: ${colors.primary};
  font-weight: 500;

  ${media.mobile} {
    font-size: 14px;
  }
`;

const PoemEnglish = styled.div`
  font-size: 13px;
  line-height: 1.4;
  opacity: 0.8;
  font-style: italic;

  ${media.mobile} {
    font-size: 12px;
  }
`;

const TryNowButton = styled.button`
  background: ${gradients.primary};
  color: ${colors.black};
  border: none;
  padding: 12px 25px;
  border-radius: 25px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  font-size: 14px;
  width: 100%;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(212, 175, 55, 0.4);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;


const HomePage: React.FC = () => {
  const [whisperExpanded, setWhisperExpanded] = useState(false);
  const [dailyFortune, setDailyFortune] = useState<any>(null);
  const [fortuneLoading, setFortuneLoading] = useState(true);
  const { setCurrentPage, setSelectedDeity, setSelectedCollection, setSelectedFortuneNumber, setCurrentConsultation, setSelectedReport } = useAppStore();
  const { t } = usePagesTranslation();

  // Fetch daily fortune on component mount
  useEffect(() => {
    const fetchDailyFortune = async () => {
      try {
        setFortuneLoading(true);
        console.log('Fetching daily fortune...');
        const fortune = await fortuneService.getDailyFortune();
        console.log('Daily fortune received:', fortune);
        setDailyFortune(fortune);
      } catch (error) {
        console.error('Failed to fetch daily fortune:', error);
        // Fall back to mock data if API fails
        setDailyFortune({
          id: 'fallback_daily',
          title: 'Daily Guidance',
          poem: mockTodaysWhisper.poem.chinese,
          fortuneLevel: 'Good Fortune',
          analysis: mockTodaysWhisper.interpretation.overview,
          deity: { id: 'guan_yin', name: 'Guan Yin' },
          number: 1,
          date: new Date().toISOString().split('T')[0],
          message: 'Today\'s guidance from the divine'
        });
      } finally {
        setFortuneLoading(false);
      }
    };

    fetchDailyFortune();
  }, []);

  const handleTryNow = () => {
    console.log('=== handleTryNow called ===');
    console.log('dailyFortune:', dailyFortune);

    if (!dailyFortune) {
      console.log('No dailyFortune data, returning early');
      return;
    }

    console.log('Daily fortune data exists, proceeding with navigation...');

    // Find the deity from our data, or use a default one
    const deity = mockDeities.find(d => d.id === dailyFortune.deity.id) || mockDeities[0];
    const collection = deity.collections[0];

    console.log('Found deity:', deity);
    console.log('Found collection:', collection);

    // Set the state to show the daily fortune analysis
    setSelectedDeity(deity);
    setSelectedCollection(collection);
    setSelectedFortuneNumber(dailyFortune.number);

    // Set current consultation data for the analysis page
    setCurrentConsultation({
      id: `daily-${dailyFortune.number}-${new Date().toISOString().split('T')[0]}`,
      deity_id: dailyFortune.deity.id,
      deity_name: dailyFortune.deity.name,
      question: 'Daily Fortune Guidance',
      selected_poem: {
        id: dailyFortune.number,
        title: dailyFortune.title || 'Daily Fortune',
        fortune: dailyFortune.fortuneLevel || 'Good Fortune',
        poem: dailyFortune.poem,
        analysis: {
          zh: {
            overview: dailyFortune.analysis || 'Today brings opportunities for growth and reflection.',
            spiritual_aspect: 'Trust in the divine guidance you receive today',
            career_aspect: 'Professional opportunities may present themselves',
            relationship_aspect: 'Harmony in relationships is favored',
            health_aspect: 'Maintain balance in all aspects of life',
            financial_aspect: 'Be mindful of your resources and opportunities'
          },
          en: {
            overview: dailyFortune.analysis || 'Today brings opportunities for growth and reflection.',
            spiritual_aspect: 'Trust in the divine guidance you receive today',
            career_aspect: 'Professional opportunities may present themselves',
            relationship_aspect: 'Harmony in relationships is favored',
            health_aspect: 'Maintain balance in all aspects of life',
            financial_aspect: 'Be mindful of your resources and opportunities'
          },
          jp: {
            overview: dailyFortune.analysis || 'Today brings opportunities for growth and reflection.',
            spiritual_aspect: 'Trust in the divine guidance you receive today',
            career_aspect: 'Professional opportunities may present themselves',
            relationship_aspect: 'Harmony in relationships is favored',
            health_aspect: 'Maintain balance in all aspects of life',
            financial_aspect: 'Be mindful of your resources and opportunities'
          }
        }
      },
      ai_interpretation: {
        summary: dailyFortune.analysis || 'Today brings opportunities for growth and reflection.',
        detailed_analysis: {
          spiritual: 'Trust in the divine guidance you receive today',
          career: 'Professional opportunities may present themselves',
          relationship: 'Harmony in relationships is favored',
          health: 'Maintain balance in all aspects of life',
          financial: 'Be mindful of your resources and opportunities'
        },
        advice: 'Follow your intuition and remain open to new possibilities',
        lucky_elements: ['Water', 'Wood', 'East Direction'],
        cautions: ['Avoid hasty decisions', 'Be patient with others']
      },
      created_at: new Date().toISOString(),
      status: 'active'
    });

    console.log('Navigating to fortune-analysis page...');
    window.location.href = '/fortune-analysis';
    console.log('Navigation triggered!');
  };

  const toggleWhisper = () => {
    setWhisperExpanded(!whisperExpanded);
  };

  const handleDemoReport = () => {
    // Set the demo report as selected and navigate to report page
    setSelectedReport(mockDemoReport);
    setCurrentPage('report');
  };


  return (
    <Layout>
      <HomeContainer>
        <HeroSection>
          <HeroContent>
            <HeroText>
              <HeroImage src="/assets/HOME_MASK.png" alt="Divine Whispers Hero" />
              <DemoReportButton onClick={handleDemoReport}>
                {t('home.knowYourFate')}
              </DemoReportButton>
            </HeroText>
            
            <TodaysWhisper expanded={whisperExpanded} onClick={toggleWhisper}>
              <MoonContainer>
                <MoonIcon>🌙</MoonIcon>
                <WhisperTitle>
                  {t('home.yourFortune')} <ExpandIcon expanded={whisperExpanded}>▾</ExpandIcon>
                </WhisperTitle>
              </MoonContainer>
              
              <WhisperCollapsed expanded={whisperExpanded}>
                {fortuneLoading
                  ? "Loading today's divine guidance..."
                  : dailyFortune?.message || mockTodaysWhisper.preview
                }
              </WhisperCollapsed>

              <WhisperExpanded expanded={whisperExpanded}>
                {fortuneLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px', color: colors.primary }}>
                    Loading your daily fortune...
                  </div>
                ) : (
                  <>
                    <WhisperPoem>
                      <PoemChinese>{dailyFortune?.poem || mockTodaysWhisper.poem.chinese}</PoemChinese>
                    </WhisperPoem>
                    <TryNowButton onClick={handleTryNow} disabled={!dailyFortune}>
                      {t('home.readWhisper')}
                    </TryNowButton>
                  </>
                )}
              </WhisperExpanded>
            </TodaysWhisper>
          </HeroContent>
        </HeroSection>

      </HomeContainer>
    </Layout>
  );
};

export default HomePage;