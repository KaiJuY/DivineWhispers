import React from 'react';
import styled from 'styled-components';
import { glow, buttonStyles, gradients, colors, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import { useAppNavigate } from '../contexts/RouterContext';
import { usePagesTranslation } from '../hooks/useTranslation';

const LandingContainer = styled.div`
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: 
    linear-gradient(135deg, rgba(10, 17, 40, 0.7) 0%, rgba(30, 39, 73, 0.6) 50%, rgba(45, 55, 72, 0.8) 100%),
    url('/assets/HOME_MASK.png') center/cover;
`;

const LandingVideo = styled.video`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
  background: linear-gradient(135deg, #0a1128 0%, #1e2749 50%, #2d3748 100%);
`;

const LandingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: ${gradients.landingOverlay};
  z-index: 2;
`;

const LandingHero = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 100;
  padding: 0 20px;
`;

const HeroTitle = styled.h1`
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 300;
  line-height: 1.2;
  margin-bottom: 40px;
  text-shadow: 
    0 0 10px rgba(212, 175, 55, 0.3),
    0 0 20px rgba(212, 175, 55, 0.2),
    2px 2px 4px rgba(0, 0, 0, 0.8);
  animation: ${glow} 3s ease-in-out infinite alternate;

  ${media.tablet} {
    margin-bottom: 30px;
  }

  ${media.mobile} {
    margin-bottom: 20px;
  }
`;

const LearnMoreButton = styled.button`
  ${buttonStyles}
  
  ${media.tablet} {
    padding: 12px 30px;
    font-size: 14px;
  }

  ${media.mobile} {
    padding: 10px 25px;
    font-size: 13px;
  }
`;

const LandingPage: React.FC = () => {
  const navigate = useAppNavigate();
  const { t } = usePagesTranslation();

  const handleLearnMore = () => {
    navigate('/home');
  };

  return (
    <Layout isLanding={true}>
      <LandingContainer>
        <LandingVideo
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          poster="/assets/HOME_MASK.png"
          onError={(e) => console.error('Video failed to load:', e)}
          onLoadStart={() => console.log('Video started loading')}
          onCanPlay={() => console.log('Video can play')}
          onLoadedData={() => console.log('Video loaded data')}
        >
          <source src="/assets/Landing.mp4" type="video/mp4" />
          <p>{t('landing.videoError')}</p>
        </LandingVideo>
        <LandingOverlay />
        <LandingHero>
          <HeroTitle>
            {t('landing.heroTitle')}
          </HeroTitle>
          <LearnMoreButton onClick={handleLearnMore}>
            {t('landing.learnMore')}
          </LearnMoreButton>
        </LandingHero>
      </LandingContainer>
    </Layout>
  );
};

export default LandingPage;