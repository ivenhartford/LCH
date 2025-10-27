import React from 'react';
import NavigationBar from './NavigationBar';
import MyCalendar from './Calendar';

function Dashboard() {
  return (
    <div style={{ padding: '20px' }}>
      <NavigationBar />
      <MyCalendar />
    </div>
  );
}

export default Dashboard;
