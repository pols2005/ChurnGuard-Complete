import React, { useEffect, useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { SubscriptionProvider } from './contexts/SubscriptionContext';
import Heading from './Heading';
import CustomerForm from './CustomerForm';
import GaugeMeter from './GaugeMeter';
import ModelProbabilities from './ModelProbabilities';
import Percentile from './Percentile';
import Explanation from './Explanation';
import Email from './Email';
import ThemeToggle from './components/ThemeToggle';
import SettingsButton from './components/SettingsButton';
import PremiumAnalytics from './components/PremiumAnalytics';
import CustomizableLayout from './components/CustomizableLayout';
import PerformanceMonitor from './components/PerformanceMonitor';

const App = () => {

  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetails, setCustomerDetails] = useState({});
  const [churnProbability, setChurnProbability] = useState(null);
  const [modelProbabilities, setModelProbabilities] = useState(null);
  const [featurePercentile, setFeaturePercentile] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [email, setEmail] = useState('');

  useEffect(() => {
    // fetch('http://localhost:5001/api/customers')
    fetch('https://churnguard-fb9w.onrender.com/api/customers')
      .then((response) => response.json())
      .then((data) => {
        const formattedCustomers = data.map((customer) => ({
          value: customer.CustomerId,
          label: `${customer.Surname} (${customer.CustomerId})`,
        }));
        setCustomers(formattedCustomers);
      });
  }, []);

  const handleCustomerSelect = (selectedOption) => {
    setSelectedCustomer(selectedOption);

    setChurnProbability(null);
    setModelProbabilities(null);
    setFeaturePercentile(null);
    setExplanation('');
    setEmail('');

    // fetch(`http://localhost:5001/api/customer/${selectedOption.value}`)
    fetch(`https://churnguard-fb9w.onrender.com/api/customer/${selectedOption.value}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setCustomerDetails(data.customer);
        }
      });

    // fetch(`http://localhost:5001/api/customer/${selectedOption.value}/churn-probability`)
    fetch(`https://churnguard-fb9w.onrender.com/api/customer/${selectedOption.value}/churn-probability`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setChurnProbability(data.average_probability);
        }
      });

    // fetch(`http://localhost:5001/api/customer/${selectedOption.value}/churn-model-probabilities`)
    fetch(`https://churnguard-fb9w.onrender.com/api/customer/${selectedOption.value}/churn-model-probabilities`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setModelProbabilities(data.model_probabilities);
        }
      });

      // fetch(`http://localhost:5001/api/customer/${selectedOption.value}/feature-percentiles`)
      fetch(`https://churnguard-fb9w.onrender.com/api/customer/${selectedOption.value}/feature-percentiles`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setFeaturePercentile(data.percentiles);
        }
      });

      // fetch(`http://localhost:5001/api/explanationwithemail/${selectedOption.value}`)
      fetch(`https://churnguard-fb9w.onrender.com/api/explanationwithemail/${selectedOption.value}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setExplanation(data.explanation);
          setEmail(data.email_content);
        }
      });

  };

  return (
    <SubscriptionProvider>
      <OrganizationProvider>
        <ThemeProvider>
          <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-screen transition-colors duration-200">
            {/* Control Panel in top-right corner */}
            <div className="fixed top-4 right-4 z-50 flex space-x-2">
              <SettingsButton />
              <ThemeToggle />
            </div>
        
        {/* Main Content */}
        <div className="flex flex-col items-center py-10 px-4">
          <Heading />
          
          <div className="max-w-6xl w-full mx-auto mt-8">
            <CustomizableLayout>
              <CustomerForm 
                customers={customers} 
                selectedCustomer={selectedCustomer} 
                customerDetails={customerDetails} 
                handleCustomerSelect={handleCustomerSelect}
              />
              
              {churnProbability && (
                <GaugeMeter churnProbability={churnProbability}/>
              )}
              
              {modelProbabilities && (
                <ModelProbabilities modelProbabilities={modelProbabilities}/>
              )}
              
              {featurePercentile && (
                <Percentile featurePercentile={featurePercentile}/>
              )}
              
              <PremiumAnalytics />
              
              {explanation && (
                <Explanation explanation={explanation}/>
              )}
              
              {email && (
                <Email email={email}/>
              )}
            </CustomizableLayout>
          </div>
        </div>
        
        {/* Performance Monitor */}
        <PerformanceMonitor />
          </div>
        </ThemeProvider>
      </OrganizationProvider>
    </SubscriptionProvider>
  );
};

export default App;
