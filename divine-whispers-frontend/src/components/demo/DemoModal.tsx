import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { useTranslation } from 'react-i18next';
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

const ThumbnailWrapper = styled.div`
  position: relative;
  display: inline-block;
  cursor: pointer;
`;

const ThumbnailImage = styled.img`
  width: 100px;
  height: auto;
  border: 2px solid ${colors.primary};
  border-radius: 4px;
  transition: transform 0.2s ease-in-out;

  ${ThumbnailWrapper}:hover & {
    transform: scale(1.1);
  }
`;

const FullImagePreview = styled.img`
  display: none;
  position: absolute;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  max-width: 600px;
  width: 600px;
  height: auto;
  border: 3px solid ${colors.primary};
  border-radius: 8px;
  z-index: 100;
  box-shadow: 0 5px 25px rgba(0,0,0,0.7);
  animation: ${fadeIn} 0.3s ease-out;

  ${ThumbnailWrapper}:hover & {
    display: block;
  }
`;

const ThumbnailsContainer = styled.div`
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 25px;
`;

interface DemoModalProps {
  onClose: () => void;
}

const DemoModal: React.FC<DemoModalProps> = ({ onClose }) => {
  const { t } = useTranslation('pages');
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      icon: t('demo.steps.overview.icon'),
      title: t('demo.steps.overview.title'),
      content: (
        <>
          <ChatText style={{ textAlign: 'center', marginBottom: '30px' }}>
            {t('demo.steps.overview.description')}
          </ChatText>
          <FeatureList>
            <FeatureItem>{t('demo.steps.overview.features.chooseDeity')}</FeatureItem>
            <FeatureItem>{t('demo.steps.overview.features.drawNumber')}</FeatureItem>
            <FeatureItem>{t('demo.steps.overview.features.receivePoem')}</FeatureItem>
            <FeatureItem>{t('demo.steps.overview.features.getInterpretation')}</FeatureItem>
          </FeatureList>
        </>
      )
    },
    {
      icon: t('demo.steps.selectDeity.icon'),
      title: t('demo.steps.selectDeity.title'),
      content: (
        <>
          <ChatText style={{ marginBottom: '20px', color: colors.white, opacity: 0.8 }}>
            {t('demo.steps.selectDeity.description')}
          </ChatText>
          <ReportMockup>
            <ReportSection>
              <ReportLabel>{t('demo.steps.selectDeity.deityLabel')}</ReportLabel>
              <ReportContent dangerouslySetInnerHTML={{ __html: t('demo.steps.selectDeity.deityList') }} />
            </ReportSection>
          </ReportMockup>
          <ChatText style={{ textAlign: 'center', color: colors.primary, fontSize: '14px', marginTop: '20px' }}>
            {t('demo.steps.selectDeity.note')}
          </ChatText>
        </>
      )
    },
    {
      icon: t('demo.steps.drawNumber.icon'),
      title: t('demo.steps.drawNumber.title'),
      content: (
        <>
          <ChatText style={{ marginBottom: '20px', color: colors.white, opacity: 0.8 }}>
            {t('demo.steps.drawNumber.description')}
          </ChatText>
          <ReportMockup>
            <ReportSection>
              <ReportLabel>{t('demo.steps.drawNumber.numberLabel')}</ReportLabel>
              <ReportContent style={{ textAlign: 'center', fontSize: '24px', padding: '30px' }}>
                {t('demo.steps.drawNumber.numberRange')}
              </ReportContent>
            </ReportSection>
          </ReportMockup>
          <ChatText style={{ textAlign: 'center', color: colors.primary, fontSize: '14px', marginTop: '20px' }}>
            {t('demo.steps.drawNumber.note')}
          </ChatText>
        </>
      )
    },
    {
      icon: t('demo.steps.readPoem.icon'),
      title: t('demo.steps.readPoem.title'),
      content: (
        <>
          <ChatText style={{ marginBottom: '20px', color: colors.white, opacity: 0.8 }}>
            {t('demo.steps.readPoem.description')}
          </ChatText>
          <ReportMockup>
            <ReportSection>
              <ReportLabel>{t('demo.steps.readPoem.poemLabel')}</ReportLabel>
              <ReportContent dangerouslySetInnerHTML={{ __html: t('demo.steps.readPoem.poemExample') }} />
            </ReportSection>
            <ReportSection>
              <ReportLabel>{t('demo.steps.readPoem.fortuneLabel')}</ReportLabel>
              <ReportContent>{t('demo.steps.readPoem.fortuneLevel')}</ReportContent>
            </ReportSection>
            <ReportSection>
              <ReportLabel>{t('demo.steps.readPoem.interpretationLabel')}</ReportLabel>
              <ReportContent>
                {t('demo.steps.readPoem.interpretationText')}
              </ReportContent>
            </ReportSection>
          </ReportMockup>
          <ThumbnailsContainer>
            <ThumbnailWrapper>
              <ThumbnailImage src="/assets/POEM.png"  alt="Poem preview" />
              <FullImagePreview src="/assets/POEM.png"  alt="Poem full view" />
            </ThumbnailWrapper>
          </ThumbnailsContainer>
        </>
      )
    },
    {
      icon: t('demo.steps.askAi.icon'),
      title: t('demo.steps.askAi.title'),
      content: (
        <>
          <ChatText style={{ marginBottom: '20px', color: colors.white, opacity: 0.8 }}>
            {t('demo.steps.askAi.description')}
          </ChatText>
          <ChatBubble isUser>
            <ChatLabel>{t('demo.steps.askAi.userLabel')}</ChatLabel>
            <ChatText>
              {t('demo.steps.askAi.userMessage')}
            </ChatText>
          </ChatBubble>
          <ChatBubble>
            <ChatLabel>{t('demo.steps.askAi.aiLabel')}</ChatLabel>
            <ChatText>
              {t('demo.steps.askAi.aiMessage')}
            </ChatText>
          </ChatBubble>
          <ChatText style={{ textAlign: 'center', color: colors.primary, fontSize: '14px', marginTop: '20px' }}>
            {t('demo.steps.askAi.note')}
          </ChatText>
          <ThumbnailsContainer>
            <ThumbnailWrapper>
              <ThumbnailImage src="/assets/CHAT.png" alt="Chat preview" />
              <FullImagePreview src="/assets/CHAT.png" alt="Chat full view" />
            </ThumbnailWrapper>
            <ThumbnailWrapper>
              <ThumbnailImage src="/assets/REPORT.png" alt="Report preview" />
              <FullImagePreview src="/assets/REPORT.png" alt="Report full view" />
            </ThumbnailWrapper>
          </ThumbnailsContainer>
        </>
      )
    },
    {
      icon: t('demo.steps.ready.icon'),
      title: t('demo.steps.ready.title'),
      content: (
        <>
          <ChatText style={{ textAlign: 'center', marginBottom: '30px' }}>
            {t('demo.steps.ready.description')}
          </ChatText>
          <FeatureList>
            <FeatureItem>{t('demo.steps.ready.features.dailyFortune')}</FeatureItem>
            <FeatureItem>{t('demo.steps.ready.features.poemsCount')}</FeatureItem>
            <FeatureItem>{t('demo.steps.ready.features.aiInterpretation')}</FeatureItem>
            <FeatureItem>{t('demo.steps.ready.features.history')}</FeatureItem>
          </FeatureList>
          <ChatText style={{ textAlign: 'center', marginTop: '30px', color: colors.primary, fontWeight: 600 }}>
            {t('demo.steps.ready.callToAction')}
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

        <Title>{t('demo.title')}</Title>
        <Subtitle>{t('demo.subtitle')}</Subtitle>

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
            {t('demo.previous')}
          </NavButton>
          {currentStep < steps.length - 1 ? (
            <NavButton primary onClick={handleNext}>
              {t('demo.next')}
            </NavButton>
          ) : (
            <NavButton primary onClick={handleGetStarted}>
              {t('demo.getStarted')}
            </NavButton>
          )}
        </ButtonGroup>
      </ModalContainer>
    </Overlay>
  );
};

export default DemoModal;