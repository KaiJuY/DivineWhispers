import React, { useState } from 'react';
import styled from 'styled-components';
import { breathe, borderBreathe, glowPulse, skewFadeIn, floatUp, colors, gradients, media, cardStyles } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { mockTodaysWhisper, mockDeities } from '../utils/mockData';

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
`;


const HeroImage = styled.img`
  width: 100%;
  max-width: 1440px;
  height: auto;
  display: block;
  margin: 0 auto;
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

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(212, 175, 55, 0.4);
  }
`;


const HomePage: React.FC = () => {
  const [whisperExpanded, setWhisperExpanded] = useState(false);
  const { setCurrentPage, setSelectedDeity, setSelectedCollection, setSelectedFortuneNumber, setCurrentConsultation } = useAppStore();

  const handleTryNow = () => {
    // Create a mock consultation based on today's whisper
    const randomDeity = mockDeities[Math.floor(Math.random() * mockDeities.length)];
    const randomCollection = randomDeity.collections[0]; // Use first collection
    const randomNumber = Math.floor(Math.random() * randomCollection.maxNumber) + 1;
    
    // Create a consultation response based on today's whisper
    const todaysConsultation = {
      id: `today_${Date.now()}`,
      deity_id: randomDeity.id,
      deity_name: randomDeity.name,
      question: "Your Divine Whisper Reading",
      selected_poem: {
        id: randomNumber,
        title: `Divine Whisper #${randomNumber}`,
        fortune: "Your Blessing",
        poem: mockTodaysWhisper.poem.chinese,
        analysis: {
          zh: {
            overview: mockTodaysWhisper.interpretation.overview,
            spiritual_aspect: mockTodaysWhisper.interpretation.advice,
            career_aspect: "專注於內心平靜和善行，將為你的事業帶來正面能量。",
            relationship_aspect: "保持心境平和，有助於改善人際關係。",
            health_aspect: "身心平衡是今日的重點。",
            financial_aspect: "善行會帶來意想不到的財富。"
          },
          en: {
            overview: mockTodaysWhisper.interpretation.overview,
            spiritual_aspect: mockTodaysWhisper.interpretation.advice,
            career_aspect: "Focus on inner peace and good deeds to bring positive energy to your career.",
            relationship_aspect: "Maintaining tranquility will help improve relationships.",
            health_aspect: "Physical and mental balance is today's focus.",
            financial_aspect: "Good deeds will bring unexpected wealth."
          },
          jp: {
            overview: mockTodaysWhisper.interpretation.overview,
            spiritual_aspect: mockTodaysWhisper.interpretation.advice,
            career_aspect: "内なる平和と善行に集中することで、キャリアにポジティブなエネルギーをもたらします。",
            relationship_aspect: "心の平穏を保つことが人間関係の改善に役立ちます。",
            health_aspect: "心身のバランスが今日の焦点です。",
            financial_aspect: "善行は予期しない富をもたらすでしょう。"
          }
        }
      },
      ai_interpretation: {
        summary: mockTodaysWhisper.interpretation.overview,
        detailed_analysis: {
          spiritual: mockTodaysWhisper.interpretation.advice,
          career: "Your professional path benefits from maintaining inner harmony and ethical practices.",
          relationship: "Peaceful energy attracts positive connections and strengthens existing bonds.",
          health: "Balance is key - nurture both body and spirit for optimal wellbeing.",
          financial: "Virtuous actions create a foundation for abundance and prosperity."
        },
        advice: mockTodaysWhisper.interpretation.advice,
        lucky_elements: mockTodaysWhisper.interpretation.lucky_elements,
        cautions: ["Avoid rushed decisions", "Stay centered in challenging moments"]
      },
      created_at: new Date().toISOString(),
      status: 'active' as const
    };
    
    // Set the state to show this consultation
    setSelectedDeity(randomDeity);
    setSelectedCollection(randomCollection);
    setSelectedFortuneNumber(randomNumber);
    setCurrentConsultation(todaysConsultation);
    setCurrentPage('fortune-analysis');
  };

  const toggleWhisper = () => {
    setWhisperExpanded(!whisperExpanded);
  };

  return (
    <Layout>
      <HomeContainer>
        <HeroSection>
          <HeroContent>
            <HeroText>
              <HeroImage src="/assets/HOME_MASK.png" alt="Divine Whispers Hero" />
            </HeroText>
            
            <TodaysWhisper expanded={whisperExpanded} onClick={toggleWhisper}>
              <MoonContainer>
                <MoonIcon>🌙</MoonIcon>
                <WhisperTitle>
                  Your Whisper <ExpandIcon expanded={whisperExpanded}>▾</ExpandIcon>
                </WhisperTitle>
              </MoonContainer>
              
              <WhisperCollapsed expanded={whisperExpanded}>
                {mockTodaysWhisper.preview}
              </WhisperCollapsed>
              
              <WhisperExpanded expanded={whisperExpanded}>
                <WhisperPoem>
                  <PoemChinese>{mockTodaysWhisper.poem.chinese}</PoemChinese>
                  <PoemEnglish>{mockTodaysWhisper.poem.english}</PoemEnglish>
                </WhisperPoem>
                <TryNowButton onClick={handleTryNow}>
                  Read Your Whisper
                </TryNowButton>
              </WhisperExpanded>
            </TodaysWhisper>
          </HeroContent>
        </HeroSection>

      </HomeContainer>
    </Layout>
  );
};

export default HomePage;