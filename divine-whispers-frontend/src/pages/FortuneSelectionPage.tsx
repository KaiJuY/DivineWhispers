import React, { useEffect } from 'react';
import styled from 'styled-components';
import { skewFadeIn, glowing, colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { mockFortuneNumbers } from '../utils/mockData';
import { usePagesTranslation } from '../hooks/useTranslation';

const FortuneContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const FortuneSection = styled.section`
  padding: 80px 40px;
  background: ${gradients.heroSection};

  ${media.tablet} {
    padding: 60px 20px;
  }

  ${media.mobile} {
    padding: 40px 20px;
  }
`;

const FortuneContent = styled.div`
  max-width: 1400px;
  min-height: 100vh;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
`;

const HeroImage = styled.img`
  width: 100%;
  max-width: 1200px;
  height: 200px;
  object-fit: cover;
  border-radius: 15px;
  margin-bottom: 30px;
  opacity: 0.8;

  ${media.tablet} {
    height: 150px;
    margin-bottom: 25px;
  }

  ${media.mobile} {
    height: 120px;
    margin-bottom: 20px;
  }
`;

const FortuneTitle = styled.h2`
  text-align: center;
  font-size: 3.5rem;
  margin-bottom: 20px;
  color: ${colors.primary};
  font-weight: 300;

  ${media.tablet} {
    font-size: 2.8rem;
    margin-bottom: 15px;
  }

  ${media.mobile} {
    font-size: 2rem;
    margin-bottom: 10px;
  }
`;

const FortuneSubtitle = styled.p`
  text-align: center;
  font-size: 1.2rem;
  margin-bottom: 60px;
  color: ${colors.white};
  opacity: 0.9;

  ${media.tablet} {
    font-size: 1.1rem;
    margin-bottom: 40px;
  }

  ${media.mobile} {
    font-size: 1rem;
    margin-bottom: 30px;
  }
`;


const NumberCard = styled.div`
  aspect-ratio: 1;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.4);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(15px);
  position: relative;
  overflow: hidden;
  animation: ${skewFadeIn} 0.4s ease-out forwards;
  
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, #d4af37, #f4e99b, #d4af37, #f4e99b);
    background-size: 400% 400%;
    animation: ${glowing} 3s ease-in-out infinite alternate;
    border-radius: inherit;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.4s ease;
  }
  
  &:hover {
    transform: scale(1.15) translateY(-5px);
    border-color: #d4af37;
    box-shadow: 0 15px 30px rgba(212, 175, 55, 0.4);
    z-index: 10;
    color: #fff;
    background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  }

  &:hover::before {
    opacity: 1;
  }

  ${media.mobile} {
    border-radius: 6px;
    
    &:hover {
      transform: scale(1.1) translateY(-3px);
    }
  }
`;

const NumbersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 15px;
  max-width: 800px;
  width: 100%;

  &:hover ${NumberCard}:not(:hover) {
    opacity: 0.6;
    transform: scale(0.9);
  }

  ${media.tablet} {
    grid-template-columns: repeat(8, 1fr);
    gap: 12px;
  }

  ${media.mobile} {
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
  }
`;

const NumberText = styled.span`
  font-size: 1.4rem;
  font-weight: 600;
  color: ${colors.primary};
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);

  ${media.mobile} {
    font-size: 1.1rem;
  }
`;

const BackButton = styled.button`
  align-self: flex-start;
  background: rgba(212, 175, 55, 0.1);
  border: 2px solid rgba(212, 175, 55, 0.3);
  color: ${colors.primary};
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(15px);
  margin-bottom: 20px;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    border-color: ${colors.primary};
    transform: translateY(-2px);
  }

  ${media.mobile} {
    padding: 10px 16px;
    font-size: 0.9rem;
  }
`;

const CollectionSection = styled.div`
  margin-bottom: 50px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const CollectionHeader = styled.div`
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 15px;
  backdrop-filter: blur(10px);
`;

const CollectionTitle = styled.h3`
  font-size: 1.8rem;
  color: ${colors.primary};
  margin-bottom: 10px;
  font-weight: 600;
  
  ${media.tablet} {
    font-size: 1.6rem;
  }
  
  ${media.mobile} {
    font-size: 1.4rem;
  }
`;

const CollectionDescription = styled.p`
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  margin-bottom: 10px;
`;

const CollectionRange = styled.div`
  color: ${colors.primary};
  font-size: 1.1rem;
  font-weight: 500;
`;

const FortuneSelectionPage: React.FC = () => {
  const { selectedDeity, setCurrentPage, setSelectedFortuneNumber, setSelectedCollection } = useAppStore();
  const { t } = usePagesTranslation();

  // Scroll to top when component mounts
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const handleBackClick = () => {
    setCurrentPage('deities');
  };

  const handleNumberSelect = (number: number, collection: any) => {
    setSelectedCollection(collection);
    setSelectedFortuneNumber(number);
    setCurrentPage('fortune-analysis');
  };

  if (!selectedDeity) {
    setCurrentPage('deities');
    return null;
  }

  return (
    <Layout>
      <FortuneContainer>
        <FortuneSection>
          <FortuneContent>
            <BackButton onClick={handleBackClick}>
              {t('fortuneSelection.backToDeities')}
            </BackButton>
            <HeroImage 
              src={`/assets${selectedDeity.imageUrl.replace(/\.(jpg|png)$/, '_W.$1')}`} 
              alt={selectedDeity.name}
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = '/assets/GuanYin_W.jpg'; // Fallback wide image
              }}
            />
            <FortuneTitle>{t('fortuneSelection.title')}</FortuneTitle>
            <FortuneSubtitle>
              {t('fortuneSelection.subtitle', { deityName: selectedDeity.name })}
            </FortuneSubtitle>
            
            {selectedDeity.collections.map((collection, collectionIndex) => {
              const availableNumbers = Array.from({length: collection.maxNumber}, (_, i) => i + 1);
              return (
                <CollectionSection key={collection.id}>
                  <CollectionHeader>
                    <CollectionTitle>{collection.name}</CollectionTitle>
                    <CollectionDescription>{collection.description}</CollectionDescription>
                    <CollectionRange>{t('fortuneSelection.numbersRange', { max: collection.maxNumber })}</CollectionRange>
                  </CollectionHeader>
                  <NumbersGrid>
                    {availableNumbers.map((number, index) => (
                      <NumberCard
                        key={`${collection.id}-${number}`}
                        style={{ animationDelay: `${(collectionIndex * 100 + index) * 0.005}s` }}
                        onClick={() => handleNumberSelect(number, collection)}
                      >
                        <NumberText>{number}</NumberText>
                      </NumberCard>
                    ))}
                  </NumbersGrid>
                </CollectionSection>
              );
            })}
          </FortuneContent>
        </FortuneSection>
      </FortuneContainer>
    </Layout>
  );
};

export default FortuneSelectionPage;