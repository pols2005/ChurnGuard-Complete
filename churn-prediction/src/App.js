import { useEffect } from 'react';

function App() {
  useEffect(() => {
    fetch('http://localhost:5001/api/data')
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => console.log(data))
      .catch((error) => console.error('Fetch error:', error));
  }, []);

  return (
    <div className="App">
      <h1>Check the console for data</h1>
    </div>
  );
}

export default App;
