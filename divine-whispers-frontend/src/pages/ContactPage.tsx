import React, { useState } from 'react';
import styled from 'styled-components';
import { colors, gradients, media, skewFadeIn } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';

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
                <ContactTitle>Contact Us</ContactTitle>
                <ContactForm onSubmit={handleSubmit}>
                  {isSubmitted && (
                    <SuccessMessage>
                      Thank you for your message! We'll get back to you soon.
                    </SuccessMessage>
                  )}
                  
                  <FormGroup>
                    <Label htmlFor="name">Name</Label>
                    <Input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Your full name"
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="your.email@example.com"
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <Label htmlFor="subject">Subject</Label>
                    <Input
                      type="text"
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      placeholder="What can we help you with?"
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <Label htmlFor="message">Message</Label>
                    <TextArea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Tell us more about your inquiry..."
                      required
                    />
                  </FormGroup>

                  <SubmitButton type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Sending...' : 'Send Message'}
                  </SubmitButton>
                </ContactForm>

                <ContactInfo>
                  <InfoTitle>Get in Touch</InfoTitle>
                  <InfoText>
                    Have questions about your fortune reading or need help with our services?
                  </InfoText>
                  <InfoText>
                    📧 Email: <a href="mailto:support@divinewhispers.com">support@divinewhispers.com</a>
                  </InfoText>
                  <InfoText>
                    🕐 Working Hours: Monday - Friday, 9:00 AM - 6:00 PM (PST)
                  </InfoText>
                  <InfoText>
                    📞 Customer Support: Available during business hours
                  </InfoText>
                  <InfoText>
                    ⏱️ Response Time: We typically respond within 4-6 hours during business days
                  </InfoText>
                </ContactInfo>
              </LeftColumn>

              <RightColumn>
                <FAQSection>
                  <FAQTitle>Frequently Asked Questions</FAQTitle>
                  
                  <FAQItem>
                    <FAQQuestion>How accurate are the fortune readings?</FAQQuestion>
                    <FAQAnswer>
                      Our fortune readings combine traditional Chinese divination methods with AI interpretation. 
                      While we strive for meaningful insights, remember that fortunes are guidance tools and 
                      should be considered alongside your own judgment.
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>How much does a fortune reading cost?</FAQQuestion>
                    <FAQAnswer>
                      Basic fortune readings are free for registered users. Premium readings with detailed 
                      analysis and personalized insights are available through our points system. 
                      Check our Purchase page for current pricing.
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>Can I get multiple readings for the same question?</FAQQuestion>
                    <FAQAnswer>
                      We recommend waiting at least 24 hours before asking the same question again. 
                      Traditional divination suggests that asking the same question repeatedly may 
                      lead to unclear or conflicting guidance.
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>Which deity should I choose for my reading?</FAQQuestion>
                    <FAQAnswer>
                      Each deity specializes in different aspects of life. Guan Yin focuses on compassion and 
                      relationships, Guan Yu on courage and career, Mazu on protection and travel. 
                      Choose based on your question's nature or trust your intuition.
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>Is my personal information secure?</FAQQuestion>
                    <FAQAnswer>
                      Yes, we take privacy seriously. Your personal information, questions, and readings are 
                      encrypted and stored securely. We never share your data with third parties without 
                      your explicit consent.
                    </FAQAnswer>
                  </FAQItem>

                  <FAQItem>
                    <FAQQuestion>Can I save my reading results?</FAQQuestion>
                    <FAQAnswer>
                      Yes! All your readings are automatically saved to your account history. 
                      You can access them anytime from your Account page to review past insights 
                      and track your spiritual journey.
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