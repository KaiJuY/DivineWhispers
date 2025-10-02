import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { colors, gradients, media } from '../../assets/styles/globalStyles';

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

const slideIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(10px);
  animation: ${fadeIn} 0.3s ease-out;
`;

const ModalContainer = styled.div`
  background: linear-gradient(135deg, rgba(20, 20, 40, 0.98) 0%, rgba(40, 20, 60, 0.98) 100%);
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 20px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 40px;
  position: relative;
  box-shadow: 0 20px 60px rgba(212, 175, 55, 0.2);
  animation: ${slideIn} 0.4s ease-out;

  ${media.tablet} {
    padding: 30px;
    max-height: 85vh;
  }

  ${media.mobile} {
    padding: 20px;
    width: 95%;
  }
`;

const CloseButton = styled.button`
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: ${colors.primary};
  font-size: 24px;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    border-color: rgba(212, 175, 55, 0.5);
    transform: rotate(90deg);
  }
`;

const Title = styled.h2`
  color: ${colors.primary};
  font-size: 32px;
  margin-bottom: 10px;
  text-align: center;
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.5);

  ${media.mobile} {
    font-size: 24px;
  }
`;

const Subtitle = styled.p`
  color: ${colors.white};
  text-align: center;
  margin-bottom: 40px;
  font-size: 16px;
  opacity: 0.9;

  ${media.mobile} {
    font-size: 14px;
    margin-bottom: 30px;
  }
`;

const StepIndicator = styled.div`
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
`;

const StepDot = styled.div<{ active: boolean; completed: boolean }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${props =>
    props.active ? colors.primary :
    props.completed ? 'rgba(212, 175, 55, 0.5)' :
    'rgba(255, 255, 255, 0.2)'};
  transition: all 0.3s ease;
  box-shadow: ${props => props.active ? '0 0 15px rgba(212, 175, 55, 0.8)' : 'none'};
`;

const DemoContent = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 30px;
  min-height: 300px;
  animation: ${fadeIn} 0.5s ease-out;

  ${media.mobile} {
    padding: 20px;
    min-height: 250px;
  }
`;

const StepTitle = styled.h3`
  color: ${colors.primary};
  font-size: 24px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;

  ${media.mobile} {
    font-size: 20px;
  }
`;

const StepIcon = styled.span`
  font-size: 32px;
`;

const ChatBubble = styled.div<{ isUser?: boolean }>`
  background: ${props => props.isUser ?
    'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%)' :
    'rgba(255, 255, 255, 0.05)'};
  border: 1px solid ${props => props.isUser ? 'rgba(212, 175, 55, 0.3)' : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 15px;
  padding: 15px 20px;
  margin-bottom: 15px;
  ${props => props.isUser ? 'margin-left: 60px;' : 'margin-right: 60px;'}
  animation: ${slideIn} 0.3s ease-out;

  ${media.mobile} {
    ${props => props.isUser ? 'margin-left: 20px;' : 'margin-right: 20px;'}
    padding: 12px 15px;
  }
`;

const ChatLabel = styled.div`
  font-size: 12px;
  color: ${colors.primary};
  margin-bottom: 5px;
  font-weight: 600;
`;

const ChatText = styled.div`
  color: ${colors.white};
  line-height: 1.6;
  font-size: 15px;

  ${media.mobile} {
    font-size: 14px;
  }
`;

const ReportMockup = styled.div`
  background: rgba(0, 0, 0, 0.4);
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 10px;
  padding: 20px;
  margin-top: 20px;

  ${media.mobile} {
    padding: 15px;
  }
`;

const ReportSection = styled.div`
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
`;

const ReportLabel = styled.div`
  color: ${colors.primary};
  font-size: 14px;
  margin-bottom: 8px;
  font-weight: 600;
`;

const ReportContent = styled.div`
  color: ${colors.white};
  font-size: 14px;
  line-height: 1.6;
  padding: 10px;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 5px;
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 15px;

  ${media.mobile} {
    flex-direction: column;
  }
`;

const NavButton = styled.button<{ primary?: boolean }>`
  padding: 12px 30px;
  border-radius: 25px;
  border: 2px solid ${props => props.primary ? colors.primary : 'rgba(255, 255, 255, 0.3)'};
  background: ${props => props.primary ? gradients.primary : 'transparent'};
  color: ${props => props.primary ? colors.black : colors.white};
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: ${props => props.primary ? '2' : '1'};

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px ${props => props.primary ?
      'rgba(212, 175, 55, 0.4)' :
      'rgba(255, 255, 255, 0.1)'};
    border-color: ${colors.primary};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  ${media.mobile} {
    padding: 10px 20px;
    font-size: 14px;
  }
`;

const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 20px 0;
`;

const FeatureItem = styled.li`
  color: ${colors.white};
  padding: 12px 0;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &:last-child {
    border-bottom: none;
  }

  &::before {
    content: '✨';
    font-size: 20px;
  }

  ${media.mobile} {
    font-size: 14px;
    padding: 10px 0;
  }
`;

interface DemoModalProps {
  onClose: () => void;
}

const DemoModal: React.FC<DemoModalProps> = ({ onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      icon: '👋',
      title: 'Welcome to Divine Whispers',
      content: (
        <>
          <ChatText style={{ textAlign: 'center', marginBottom: '30px' }}>
            Discover how our AI-powered fortune-telling system combines ancient wisdom with modern technology to provide personalized guidance.
          </ChatText>
          <FeatureList>
            <FeatureItem>800+ authentic temple fortune poems from 8+ deities</FeatureItem>
            <FeatureItem>AI-powered personalized interpretations</FeatureItem>
            <FeatureItem>Multilingual support (Chinese, English, Japanese)</FeatureItem>
            <FeatureItem>Comprehensive life aspect analysis</FeatureItem>
          </FeatureList>
        </>
      )
    },
    {
      icon: '💬',
      title: 'Step 1: Ask Your Question',
      content: (
        <>
          <ChatText style={{ marginBottom: '20px', color: colors.white, opacity: 0.8 }}>
            Start by asking a question about your life, career, relationships, or any aspect you seek guidance on.
          </ChatText>
          <ChatBubble isUser>
            <ChatLabel>You</ChatLabel>
            <ChatText>
              "I'm considering a career change. Should I take the new job offer or stay in my current position?"
            </ChatText>
          </ChatBubble>
          <ChatText style={{ textAlign: 'center', color: colors.primary, fontSize: '14px', marginTop: '20px' }}>
            Our system uses semantic search to find the most relevant fortune poem for your situation
          </ChatText>
        </>
      )
    },
    {
      icon: '🎴',
      title: 'Step 2: Receive Your Fortune',
      content: (
        <>
          <ChatBubble>
            <ChatLabel>Divine Whispers AI</ChatLabel>
            <ChatText>
              Based on your question, I've selected Fortune #42 from Guan Yin (觀音籤第四十二籤) - 上上籤 (Superior Fortune)
            </ChatText>
          </ChatBubble>
          <ReportMockup>
            <ReportSection>
              <ReportLabel>📜 Fortune Poem</ReportLabel>
              <ReportContent>
                天邊明月照人間 / 四海五湖皆照見 /
                萬里無雲天正朗 / 有如明鏡掛當空
              </ReportContent>
            </ReportSection>
            <ReportSection>
              <ReportLabel>🌟 Fortune Level</ReportLabel>
              <ReportContent>上上籤 (Superior Fortune) - Highly auspicious</ReportContent>
            </ReportSection>
          </ReportMockup>
        </>
      )
    },
    {
      icon: '📊',
      title: 'Step 3: AI-Powered Analysis',
      content: (
        <>
          <ChatText style={{ marginBottom: '20px', color: colors.white, opacity: 0.8 }}>
            Our AI analyzes the fortune poem in the context of your specific question and provides detailed guidance across multiple life aspects.
          </ChatText>
          <ReportMockup>
            <ReportSection>
              <ReportLabel>💼 Career Aspect</ReportLabel>
              <ReportContent>
                The moon illuminating all lands suggests clarity and visibility. This is an excellent time for career advancement. The new opportunity will bring recognition and success.
              </ReportContent>
            </ReportSection>
            <ReportSection>
              <ReportLabel>🎯 Recommendation</ReportLabel>
              <ReportContent>
                Take the new position with confidence. Like the bright moon clearing away darkness, this change will bring clarity to your professional path.
              </ReportContent>
            </ReportSection>
            <ReportSection>
              <ReportLabel>⚠️ Caution</ReportLabel>
              <ReportContent>
                Ensure thorough preparation. The "cloudless sky" reminds you to maintain transparency and honesty in negotiations.
              </ReportContent>
            </ReportSection>
          </ReportMockup>
        </>
      )
    },
    {
      icon: '🎉',
      title: 'Ready to Try?',
      content: (
        <>
          <ChatText style={{ textAlign: 'center', marginBottom: '30px' }}>
            Experience the power of AI-enhanced ancient wisdom for yourself!
          </ChatText>
          <FeatureList>
            <FeatureItem>Get started with free daily fortune reading</FeatureItem>
            <FeatureItem>Ask unlimited questions with premium account</FeatureItem>
            <FeatureItem>Save and review your consultation history</FeatureItem>
            <FeatureItem>Access detailed reports and insights</FeatureItem>
          </FeatureList>
          <ChatText style={{ textAlign: 'center', marginTop: '30px', color: colors.primary, fontWeight: 600 }}>
            Click "Get Started" below to begin your journey! ✨
          </ChatText>
        </>
      )
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGetStarted = () => {
    onClose();
    // Scroll to daily fortune section or navigate
    const fortuneSection = document.querySelector('[data-section="daily-fortune"]');
    if (fortuneSection) {
      fortuneSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <Overlay onClick={onClose}>
      <ModalContainer onClick={(e) => e.stopPropagation()}>
        <CloseButton onClick={onClose}>×</CloseButton>

        <Title>How Divine Whispers Works</Title>
        <Subtitle>Discover personalized fortune-telling powered by AI</Subtitle>

        <StepIndicator>
          {steps.map((_, index) => (
            <StepDot
              key={index}
              active={index === currentStep}
              completed={index < currentStep}
            />
          ))}
        </StepIndicator>

        <DemoContent>
          <StepTitle>
            <StepIcon>{steps[currentStep].icon}</StepIcon>
            {steps[currentStep].title}
          </StepTitle>
          {steps[currentStep].content}
        </DemoContent>

        <ButtonGroup>
          <NavButton onClick={handlePrev} disabled={currentStep === 0}>
            ← Previous
          </NavButton>
          {currentStep < steps.length - 1 ? (
            <NavButton primary onClick={handleNext}>
              Next →
            </NavButton>
          ) : (
            <NavButton primary onClick={handleGetStarted}>
              Get Started ✨
            </NavButton>
          )}
        </ButtonGroup>
      </ModalContainer>
    </Overlay>
  );
};

export default DemoModal;
