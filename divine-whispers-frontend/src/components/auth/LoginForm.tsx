import React, { useState } from 'react';
import styled from 'styled-components';
import { colors } from '../../assets/styles/globalStyles';
import useAppStore from '../../stores/appStore';
import { LoginCredentials } from '../../types';

const FormContainer = styled.div`
  width: 100%;
  margin: 0 auto;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  backdrop-filter: none;
`;

const Title = styled.h2`
  color: ${colors.primary};
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1.5rem;
`;

const InputGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  color: ${colors.white};
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 6px;
  color: ${colors.white};
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: ${colors.primary};
    background: rgba(255, 255, 255, 0.15);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  color: ${colors.black};
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const ErrorMessage = styled.div`
  color: #ff6b6b;
  text-align: center;
  margin-bottom: 1rem;
  font-size: 0.9rem;
`;

const SuccessMessage = styled.div`
  color: #51cf66;
  text-align: center;
  margin-bottom: 1rem;
  font-size: 0.9rem;
`;

const TestCredentials = styled.div`
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
`;

const TestTitle = styled.div`
  color: ${colors.primary};
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
`;

const TestInfo = styled.div`
  color: ${colors.white};
  font-size: 0.8rem;
  line-height: 1.4;
`;

interface LoginFormProps {
  onSuccess?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login, auth } = useAppStore();
  const [formData, setFormData] = useState<LoginCredentials>({
    email: '',
    password: ''
  });
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.email || !formData.password) {
      setError('Please fill in all fields');
      return;
    }

    try {
      const authState = await login(formData);
      setSuccess(`Login successful! Welcome ${authState.user?.username || 'User'}`);
      
      if (onSuccess) {
        setTimeout(onSuccess, 1000);
      }
    } catch (error: any) {
      setError(error.message || 'Login failed');
    }
  };

  const fillTestCredentials = () => {
    setFormData({
      email: 'test@example.com',
      password: 'testpassword'
    });
  };

  return (
    <FormContainer>
      <Title>Divine Whispers Login</Title>
      
      <TestCredentials>
        <TestTitle>Test Backend Connection</TestTitle>
        <TestInfo>
          Click "Use Test Credentials" to test with demo account, or enter your own credentials.
          This will verify the backend API connection.
        </TestInfo>
        <Button 
          type="button" 
          onClick={fillTestCredentials}
          style={{ marginTop: '0.5rem', fontSize: '0.8rem', padding: '0.5rem' }}
        >
          Use Test Credentials
        </Button>
      </TestCredentials>

      <form onSubmit={handleSubmit}>
        <InputGroup>
          <Label htmlFor="email">Email</Label>
          <Input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            placeholder="Enter your email"
            required
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="password">Password</Label>
          <Input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            placeholder="Enter your password"
            required
          />
        </InputGroup>

        {error && <ErrorMessage>{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}

        <Button type="submit" disabled={auth.loading}>
          {auth.loading ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>
    </FormContainer>
  );
};

export default LoginForm;