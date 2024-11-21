import React from 'react';
import Select from 'react-select';

const CustomerForm = ({customers, selectedCustomer, customerDetails, handleCustomerSelect}) => {

  return (
    <form
      className="p-8 rounded-lg max-w-4xl w-full mx-auto"
      style={{
        background: `linear-gradient(135deg, #01497c, #014f86, #2a6f97, #2c7da0, #468faf)`,
      }}
    >
      {/* Dropdown to Select Customer */}
      <div className="mb-6">
        <label className="block text-lg font-semibold mb-2 text-white">Select Customer</label>
        <Select
          options={customers}
          onChange={handleCustomerSelect}
          placeholder="Choose a Customer"
          className="text-black"
        />
      </div>

      {selectedCustomer && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column 1 */}
          <div>
            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Credit Score</label>
              <input
                type="number"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.CreditScore || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Location</label>
              <input
                type="text"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.Geography || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Gender</label>
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="gender"
                    value="Male"
                    checked={customerDetails.Gender === 'Male'}
                    readOnly
                    className="w-5 h-5 accent-blue-900"
                  />
                  <span className="text-white">Male</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="gender"
                    value="Female"
                    checked={customerDetails.Gender === 'Female'}
                    readOnly
                    className="w-5 h-5 accent-blue-900"
                  />
                  <span className="text-white">Female</span>
                </label>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Age</label>
              <input
                type="number"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.Age || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Tenure(years)</label>
              <input
                type="number"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.Tenure || ''}
                readOnly
              />
            </div>
          </div>

          {/* Column 2 */}
          <div>
            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Balance</label>
              <input
                type="number"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.Balance || ''}
                readOnly
              />
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Number of Products</label>
              <input
                type="number"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.NumOfProducts || ''}
                readOnly
              />
            </div>

            <div className="mb-4 flex items-center">
              <input
                type="checkbox"
                className="w-5 h-5 accent-blue-900 mr-2"
                checked={customerDetails.HasCrCard === 1}
                readOnly
              />
              <label className="text-lg font-semibold text-white">Has Credit Card?</label>
            </div>

            <div className="mb-4 flex items-center">
              <input
                type="checkbox"
                className="w-5 h-5 accent-blue-900 mr-2"
                checked={customerDetails.IsActiveMember === 1}
                readOnly
              />
              <label className="text-lg font-semibold text-white">Is Active Member?</label>
            </div>

            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2 text-white">Estimated Salary</label>
              <input
                type="number"
                className="w-full p-3 bg-white bg-opacity-20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={customerDetails.EstimatedSalary || ''}
                readOnly
              />
            </div>
          </div>
        </div>
      )}
    </form>
  );
};

export default CustomerForm;
