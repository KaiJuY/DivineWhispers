import React from 'react';
import styled from 'styled-components';
import { skewFadeIn, colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { mockDeities } from '../utils/mockData';

const DeitiesContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const DeitiesSection = styled.section`
  padding: 80px 40px;
  background: ${gradients.heroSection};

  ${media.tablet} {
    padding: 60px 20px;
  }

  ${media.mobile} {
    padding: 40px 20px;
  }
`;

const DeitiesContent = styled.div`
  max-width: 1400px;
  min-height: 100vh;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const DeitiesTitle = styled.h2`
  text-align: center;
  font-size: 3.5rem;
  margin-bottom: 60px;
  color: ${colors.white};
  font-weight: 300;

  ${media.tablet} {
    font-size: 2.8rem;
    margin-bottom: 40px;
  }

  ${media.mobile} {
    font-size: 2rem;
    margin-bottom: 30px;
  }
`;

const DeitiesGrid = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  flex-wrap: wrap;

  &:hover .belief-card:not(:hover) {
    flex: 0.6;
    opacity: 0.5;
    transform: skewX(-10deg) scale(0.9);
  }

  ${media.tablet} {
    gap: 15px;
    padding: 20px 0;
  }

  ${media.mobile} {
    flex-direction: column;
    gap: 20px;
    
    &:hover .belief-card:not(:hover) {
      flex: 1;
      opacity: 1;
      transform: skewX(0deg) scale(1);
    }
  }
`;

const DeityCard = styled.div<{ image: string }>`
  flex: 1;
  width: 250px;
  height: 450px;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.4);
  transform: skewX(-10deg);
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(15px);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  animation: ${skewFadeIn} 0.8s ease-out forwards;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -50px;
    width: 150%;
    height: 150%;
    background-image: url(${props => props.image});
    background-size: cover;
    background-position: center 50%;
    background-repeat: no-repeat;
    opacity: 0.8;
    transition: all 0.3s ease;
    z-index: 1;
  }

  &:hover {
    flex: 1.2;
    transform: skewX(-10deg) scale(1.1) translateY(-15px);
    border-color: ${colors.primary};
    box-shadow: 0 30px 60px rgba(212, 175, 55, 0.5);
    z-index: 10;
    position: relative;

    &::before {
      opacity: 1;
    }
  }

  ${media.mobile} {
    width: 100%;
    max-width: 300px;
    transform: skewX(0deg);
    
    &:hover {
      transform: skewX(0deg) scale(1.05) translateY(-10px);
      flex: 1;
    }
  }
`;

const CardContent = styled.div`
  transform: skewX(10deg) translateX(-10px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  z-index: 3;
  position: relative;
  padding-bottom: 10px;
  text-align: center;
  width: 100%;
`;


const CardTitle = styled.h3`
  color: #d4af37;
  margin-bottom: 8px;
  font-size: 1.5rem;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);

  ${media.mobile} {
    font-size: 1.2rem;
  }
`;

const CardDescription = styled.p`
  opacity: 0.9;
  line-height: 1.3;
  font-size: 1.2rem;
  text-align: center;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.7);

  ${media.mobile} {
    font-size: 1rem;
  }
`;

// Fixed design to match mockup
const DeitiesPage: React.FC = () => {
  const { setCurrentPage, setSelectedDeity, setSelectedCollection } = useAppStore();

  const handleDeitySelect = (deity: any) => {
    setSelectedDeity(deity);
    setCurrentPage('fortune-selection');
  };

  return (
    <Layout>
      <DeitiesContainer>
        <DeitiesSection>
          <DeitiesContent>
            <DeitiesTitle>Choose your belief</DeitiesTitle>
            <DeitiesGrid>
              {mockDeities.map((deity, index) => (
                <DeityCard 
                  key={deity.id} 
                  image={`/assets${deity.imageUrl}`}
                  style={{ animationDelay: `${index * 0.2}s` }}
                  className="belief-card"
                  onClick={() => handleDeitySelect(deity)}
                >
                  <CardContent>
                    {Array.isArray(deity.description) ? (
                      deity.description.map((line, idx) => (
                        <CardDescription key={idx}>{line}</CardDescription>
                      ))
                    ) : (
                      <CardDescription>{deity.description}</CardDescription>
                    )}
                    <CardTitle>{deity.name}</CardTitle>
                  </CardContent>
                </DeityCard>
              ))}
            </DeitiesGrid>
          </DeitiesContent>
        </DeitiesSection>
      </DeitiesContainer>
    </Layout>
  );
};

export default DeitiesPage;