import React from "react";

const CompanyDashboard: React.FC = () => {
  return (
    <div style={{ padding: "20px" }}>
      <h1>Company Dashboard</h1>

      <p>
        Welcome to the company dashboard. Here you can manage your company, 
        branches, employees, buses, routes, schedules, and ticket sales.
      </p>

      <div style={{ marginTop: "20px", fontSize: "14px", color: "#555" }}>
        <p>✔ Company Overview</p>
        <p>✔ Branches Management</p>
        <p>✔ Employee Management</p>
        <p>✔ Buses & Routes Management</p>
        <p>✔ Ticket Sales Overview</p>
        <p>✔ Reports & Analytics</p>
      </div>
    </div>
  );
};

export default CompanyDashboard;
