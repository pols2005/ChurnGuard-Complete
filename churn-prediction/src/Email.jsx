const Email = ({ email }) => {
  // Split email content into lines
  const emailLines = email.split('\n');

  return (
    <div
      className="p-8 rounded-lg max-w-6xl w-full mx-auto mt-3"
      style={{
        background: `linear-gradient(135deg, #01497c, #014f86, #2a6f97, #2c7da0, #468faf)`,
      }}
    >
      <div className="text-2xl font-semibold mb-3">Generated Email to Customer:</div>
      <div className="text-gray-100">
        {emailLines.map((line, index) => (
          // Render each line as a separate <p> element
          <p key={index} className="mb-2">
            {line.trim()}
          </p>
        ))}
      </div>
    </div>
  );
};

export default Email;
