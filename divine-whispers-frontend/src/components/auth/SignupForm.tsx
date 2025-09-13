import React, { useState } from 'react';
import styled from 'styled-components';
import { colors } from '../../assets/styles/globalStyles';
import useAppStore from '../../stores/appStore';
import { RegisterCredentials } from '../../types';

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

const Select = styled.select`
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

  option {
    background: rgba(10, 17, 40, 0.95);
    color: ${colors.white};
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

interface SignupFormProps {
  onSuccess?: () => void;
}

const SignupForm: React.FC<SignupFormProps> = ({ onSuccess }) => {
  const { register, auth } = useAppStore();
  const [formData, setFormData] = useState<RegisterCredentials>({
    email: '',
    password: '',
    confirm_password: '',
    username: '',
    birth_date: '',
    gender: '',
    location: ''
  });
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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

    // Basic validation
    if (!formData.email || !formData.password || !formData.confirm_password) {
      setError('Please fill in all required fields');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    try {
      const authState = await register(formData);
      setSuccess(`Registration successful! Welcome ${authState.user?.username || 'User'}`);
      
      if (onSuccess) {
        setTimeout(onSuccess, 1000);
      }
    } catch (error: any) {
      setError(error.message || 'Registration failed');
    }
  };

  const fillTestCredentials = () => {
    setFormData({
      email: 'newuser@example.com',
      password: 'password123',
      confirm_password: 'password123',
      username: 'NewUser',
      birth_date: '1990-01-01',
      gender: 'Male',
      location: 'San Francisco, CA'
    });
  };

  return (
    <FormContainer>
      <Title>Create Divine Whispers Account</Title>
      
      <TestCredentials>
        <TestTitle>Test Registration</TestTitle>
        <TestInfo>
          Click "Use Test Data" to auto-fill the form with sample data, or enter your own information.
          This will test the backend registration API.
        </TestInfo>
        <Button 
          type="button" 
          onClick={fillTestCredentials}
          style={{ marginTop: '0.5rem', fontSize: '0.8rem', padding: '0.5rem' }}
        >
          Use Test Data
        </Button>
      </TestCredentials>

      <form onSubmit={handleSubmit}>
        <InputGroup>
          <Label htmlFor="email">Email *</Label>
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
          <Label htmlFor="username">Username *</Label>
          <Input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            placeholder="Choose a username"
            required
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="password">Password *</Label>
          <Input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            placeholder="Enter a password (min 6 characters)"
            required
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="confirm_password">Confirm Password *</Label>
          <Input
            type="password"
            id="confirm_password"
            name="confirm_password"
            value={formData.confirm_password}
            onChange={handleInputChange}
            placeholder="Confirm your password"
            required
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="birth_date">Birth Date</Label>
          <Input
            type="date"
            id="birth_date"
            name="birth_date"
            value={formData.birth_date}
            onChange={handleInputChange}
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="gender">Gender</Label>
          <Select
            id="gender"
            name="gender"
            value={formData.gender}
            onChange={handleInputChange}
          >
            <option value="">Select gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
            <option value="Prefer not to say">Prefer not to say</option>
          </Select>
        </InputGroup>

        <InputGroup>
          <Label htmlFor="location">Location</Label>
          <Input
            type="text"
            id="location"
            name="location"
            value={formData.location}
            onChange={handleInputChange}
            placeholder="Your location (optional)"
          />
        </InputGroup>

        {error && <ErrorMessage>{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}

        <Button type="submit" disabled={auth.loading}>
          {auth.loading ? 'Creating Account...' : 'Create Account'}
        </Button>
      </form>
    </FormContainer>
  );
};

export default SignupForm;