import React, { useEffect, useState } from 'react';
import Heading from './Heading';
import CustomerForm from './CustomerForm';

const App = () => {

  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetails, setCustomerDetails] = useState({});

  useEffect(() => {
    fetch('http://localhost:5001/api/customers')
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
    fetch(`http://localhost:5001/api/customer/${selectedOption.value}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setCustomerDetails(data.customer);
        }
      });
  };

  return (
    <div className="bg-gray-900 text-gray-100 min-h-screen flex flex-col items-center py-10">
      <Heading />
      <CustomerForm customers={customers} selectedCustomer={selectedCustomer} customerDetails={customerDetails} handleCustomerSelect={handleCustomerSelect}/>
    </div>
  );
};

export default App;
