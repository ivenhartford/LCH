import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login({ setUser }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    if (response.ok) {
      const user = await fetch('/api/check_session').then(res => res.json());
      setUser(user);
      navigate('/');
    } else {
      alert('Login failed');
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="username">Username</label>
      <input id="username" type="text" onChange={e => setUsername(e.target.value)} />
      <label htmlFor="password">Password</label>
      <input id="password" type="password" onChange={e => setPassword(e.target.value)} />
      <div>
        <button type="submit">Submit</button>
      </div>
    </form>
  )
}

export default Login;
