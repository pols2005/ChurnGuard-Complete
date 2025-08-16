import React from 'react';
import Select from 'react-select';

const CustomerForm = ({customers, selectedCustomer, customerDetails, handleCustomerSelect}) => {
  
  // Custom styles for react-select to support dark mode
  const selectStyles = {
    control: (styles, { isFocused }) => ({
      ...styles,
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      borderColor: isFocused ? 'var(--brand-primary)' : 'rgba(255, 255, 255, 0.3)',
      boxShadow: isFocused ? `0 0 0 1px var(--brand-primary)` : 'none',
      '&:hover': {
        borderColor: 'var(--brand-primary)',
      },
      minHeight: '48px',
    }),
    menu: (styles) => ({
      ...styles,
      backgroundColor: 'var(--surface)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
    }),
    option: (styles, { isFocused, isSelected }) => ({
      ...styles,
      backgroundColor: isSelected 
        ? 'var(--brand-primary)' 
        : isFocused 
        ? 'rgba(255, 255, 255, 0.1)' 
        : 'transparent',
      color: 'inherit',
      '&:hover': {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
      },
    }),
    singleValue: (styles) => ({
      ...styles,
      color: 'white',
    }),
    placeholder: (styles) => ({
      ...styles,
      color: 'rgba(255, 255, 255, 0.7)',
    }),
  };

  return (
    <form className="p-8 rounded-xl max-w-6xl w-full mx-auto bg-gradient-to-br from-primary/20 via-secondary/20 to-primary/30 dark:from-primary/10 dark:via-secondary/10 dark:to-primary/20 backdrop-blur-sm border border-white/20 dark:border-gray-700/50 shadow-2xl">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 rounded-xl"></div>
      <div className="relative z-10">
        {/* Dropdown to Select Customer */}
        <div className="mb-6">
          <label className="block text-lg font-semibold mb-3 text-white dark:text-gray-200">Select Customer</label>
          <Select
            options={customers}
            onChange={handleCustomerSelect}
            placeholder="Choose a Customer"
            styles={selectStyles}
            className="react-select-container"
            classNamePrefix="react-select"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column 1 */}
          <div>
            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Credit Score</label>
              <input
                type="number"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.CreditScore || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Location</label>
              <input
                type="text"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.Geography || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Gender</label>
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="gender"
                    value="Male"
                    checked={customerDetails.Gender === 'Male'}
                    readOnly
                    className="w-5 h-5 text-primary focus:ring-primary focus:ring-2"
                  />
                  <span className="text-white dark:text-gray-200">Male</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="gender"
                    value="Female"
                    checked={customerDetails.Gender === 'Female'}
                    readOnly
                    className="w-5 h-5 text-primary focus:ring-primary focus:ring-2"
                  />
                  <span className="text-white dark:text-gray-200">Female</span>
                </label>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Age</label>
              <input
                type="number"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.Age || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Tenure(years)</label>
              <input
                type="number"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.Tenure || ''}
                readOnly
              />
            </div>
          </div>

          {/* Column 2 */}
          <div>
            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Balance</label>
              <input
                type="number"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.Balance || (selectedCustomer ? 0 : '')}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Number of Products</label>
              <input
                type="number"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.NumOfProducts || ''}
                readOnly
              />
            </div>

            <div className="mb-4 flex items-center">
              <input
                type="checkbox"
                className="w-5 h-5 text-primary focus:ring-primary focus:ring-2 mr-3"
                checked={customerDetails.HasCrCard === 1}
                readOnly
              />
              <label className="text-lg font-semibold text-white dark:text-gray-200">Has Credit Card?</label>
            </div>

            <div className="mb-4 flex items-center">
              <input
                type="checkbox"
                className="w-5 h-5 text-primary focus:ring-primary focus:ring-2 mr-3"
                checked={customerDetails.IsActiveMember === 1}
                readOnly
              />
              <label className="text-lg font-semibold text-white dark:text-gray-200">Is Active Member?</label>
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white dark:text-gray-200">Estimated Salary</label>
              <input
                type="number"
                className="w-full p-3 bg-white/20 dark:bg-gray-800/50 text-white dark:text-gray-200 rounded-lg border border-white/30 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200"
                value={customerDetails.EstimatedSalary || ''}
                readOnly
              />
            </div>
          </div>
        </div>
      </div>
    </form>
  );
};

export default CustomerForm;
