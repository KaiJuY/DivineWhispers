import React, { useState } from 'react';
import styled from 'styled-components';
import { colors, gradients, media, skewFadeIn } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import { usePagesTranslation, useFormsTranslation } from '../hooks/useTranslation';

const ContactContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const ContactSection = styled.section`
  padding: 120px 40px 80px;
  background: ${gradients.heroSection};

  ${media.tablet} {
    padding: 100px 20px 60px;
  }

  ${media.mobile} {
    padding: 80px 20px 40px;
  }
`;

const ContactContent = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const ContactTitle = styled.h2`
  text-align: center;
  font-size: 2rem;
  margin-bottom: 30px;
  color: ${colors.primary};
  font-weight: 300;

  ${media.tablet} {
    font-size: 2.8rem;
    margin-bottom: 30px;
  }

  ${media.mobile} {
    font-size: 2rem;
    margin-bottom: 25px;
    text-align: center;
  }
`;

const ContactForm = styled.form`
  width: 100%;
  max-width: 600px;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.4);
  border-radius: 20px;
  padding: 40px;
  backdrop-filter: blur(15px);

  ${media.mobile} {
    padding: 30px 20px;
  }
`;

const FormGroup = styled.div`
  margin-bottom: 25px;
`;

const Label = styled.label`
  display: block;
  color: ${colors.primary};
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
`;

const Input = styled.input`
  width: 100%;
  padding: 15px 20px;
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.2);
  color: ${colors.white};
  font-size: 16px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);

  &:focus {
    outline: none;
    border-color: ${colors.primary};
    background: rgba(0, 0, 0, 0.3);
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: 15px 20px;
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.2);
  color: ${colors.white};
  font-size: 16px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  min-height: 120px;
  resize: vertical;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: ${colors.primary};
    background: rgba(0, 0, 0, 0.3);
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const SubmitButton = styled.button`
  width: 100%;
  background: ${gradients.primary};
  color: ${colors.black};
  border: none;
  padding: 18px 25px;
  border-radius: 25px;
  cursor: pointer;
  font-weight: bold;
  font-size: 16px;
  transition: all 0.3s ease;
  margin-top: 10px;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(212, 175, 55, 0.4);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const ParallelSection = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  width: 100%;
  max-width: 1400px;
  margin-top: 50px;
  align-items: start;

  ${media.tablet} {
    grid-template-columns: 1fr;
    gap: 40px;
  }
`;

const LeftColumn = styled.div`
  width: 100%;
`;

const RightColumn = styled.div`
  width: 100%;
`;

const ContactInfo = styled.div`
  color: ${colors.white};
  margin-top: 40px;
`;

const InfoTitle = styled.h3`
  color: ${colors.primary};
  font-size: 1.5rem;
  margin-bottom: 20px;
  font-weight: 500;
`;

const InfoText = styled.p`
  font-size: 1rem;
  line-height: 1.6;
  opacity: 0.9;
  margin-bottom: 10px;

  a {
    color: ${colors.primary};
    text-decoration: none;
    transition: all 0.3s ease;

    &:hover {
      text-decoration: underline;
    }
  }
`;

const SuccessMessage = styled.div`
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(76, 175, 80, 0.1) 100%);
  border: 2px solid rgba(76, 175, 80, 0.4);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 25px;
  text-align: center;
  color: #4caf50;
  font-weight: 500;
`;

const FAQSection = styled.div`
  width: 100%;
`;

const FAQTitle = styled.h3`
  color: ${colors.primary};
  font-size: 2rem;
  margin-bottom: 30px;
  text-align: center;
  font-weight: 500;

  ${media.tablet} {
    font-size: 1.8rem;
  }

  ${media.mobile} {
    font-size: 1.5rem;
    margin-bottom: 25px;
  }
`;

const FAQItem = styled.div`
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.08) 0%, rgba(212, 175, 55, 0.02) 100%);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(212, 175, 55, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(212, 175, 55, 0.1);
  }

  ${media.mobile} {
    padding: 20px;
  }
`;

const FAQQuestion = styled.h4`
  color: ${colors.primary};
  font-size: 1.2rem;
  margin-bottom: 12px;
  font-weight: 600;
  line-height: 1.4;

  ${media.mobile} {
    font-size: 1.1rem;
  }
`;

const FAQAnswer = styled.p`
  color: ${colors.white};
  font-size: 1rem;
  line-height: 1.6;
  opacity: 0.9;
  margin: 0;

  ${media.mobile} {
    font-size: 0.95rem;
  }
`;

const ContactPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const { t: tPage } = usePagesTranslation();
  const { t: tForm } = useFormsTranslation();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
      setFormData({ name: '', email: '', subject: '', message: '' });
    }, 1500);
  };

  return (
    <Layout>
      <ContactContainer>
        <ContactSection>
          <ContactContent>
            <ParallelSection>
              <LeftColumn>
                <ContactTitle>{tPage('contact.title')}</ContactTitle>
                <ContactForm onSubmit={handleSubmit}>
                  {isSubmitted && (
                    <SuccessMessage>
                      {tPage('contact.thankYouMessage')}
                    </SuccessMessage>
                  )}
                  
                  <FormGroup>
                    <Label htmlFor="name">{tForm('labels.name')}</Label>
                    <Input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder={tForm('placeholders.name')}
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <Label htmlFor="email">{tForm('labels.email')}</Label>
                    <Input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder={tForm('placeholders.email')}
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <Label htmlFor="subject">{tForm('labels.subject')}</Label>
                    <Input
                      type="text"
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      placeholder={tForm('placeholders.subject')}
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <Label htmlFor="message">{tForm('labels.message')}</Label>
                    <TextArea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder={tForm('placeholders.message')}
                      required
                    />
                  </FormGroup>

                  <SubmitButton type="submit" disabled={isSubmitting}>
                    {isSubmitting ? tPage('contact.sending') : tPage('contact.sendMessage')}
                  </SubmitButton>
                </ContactForm>

                <ContactInfo>
                  <InfoTitle>{tPage('contact.getInTouch')}</InfoTitle>
                  <InfoText>
                    {tPage('contact.haveQuestions')}
                  </InfoText>
                  <InfoText>
                    📧 Email: <a href="mailto:support@divinewhispers.com">support@divinewhispers.com</a>
                  </InfoText>
                  <InfoText>
                    🕐 {tPage('contact.workingHours')}
                  </InfoText>
                  <InfoText>
                    📞 {tPage('contact.customerSupport')}
                  </InfoText>
                  <InfoText>
                    ⏱️ {tPage('contact.responseTime')}
                  </InfoText>
                </ContactInfo>
              </LeftColumn>

              <RightColumn>
                <FAQSection>
                  <FAQTitle>{tPage('contact.faqTitle')}</FAQTitle>
                  
                  <FAQItem>
                    <FAQQuestion>{tForm('faq.q1')}</FAQQuestion>
                    <FAQAnswer>
                      {tForm('faq.a1')}
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>{tForm('faq.q2')}</FAQQuestion>
                    <FAQAnswer>
                      {tForm('faq.a2')}
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>{tForm('faq.q3')}</FAQQuestion>
                    <FAQAnswer>
                      {tForm('faq.a3')}
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>{tForm('faq.q4')}</FAQQuestion>
                    <FAQAnswer>
                      {tForm('faq.a4')}
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>{tForm('faq.q5')}</FAQQuestion>
                    <FAQAnswer>
                      {tForm('faq.a5')}
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>{tForm('faq.q6')}</FAQQuestion>
                    <FAQAnswer>
                      {tForm('faq.a6')}
                    </FAQAnswer>
                  </FAQItem>
                </FAQSection>
              </RightColumn>
            </ParallelSection>
          </ContactContent>
        </ContactSection>
      </ContactContainer>
    </Layout>
  );
};

export default ContactPage;