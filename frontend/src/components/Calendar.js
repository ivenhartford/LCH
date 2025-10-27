import React, { useState, useEffect } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import Modal from 'react-modal';
import 'react-big-calendar/lib/css/react-big-calendar.css';

if (process.env.NODE_ENV !== 'test') {
  Modal.setAppElement('#root');
}

const localizer = momentLocalizer(moment);

const MyCalendar = () => {
  const [events, setEvents] = useState([]);
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const fetchAppointments = async () => {
    const response = await fetch('/api/appointments');
    if (response.ok) {
      const data = await response.json();
      const formattedEvents = data.map((apt) => ({
        ...apt,
        start: new Date(apt.start),
        end: new Date(apt.end),
      }));
      setEvents(formattedEvents);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleSelectSlot = (slotInfo) => {
    setSelectedSlot(slotInfo);
    setModalIsOpen(true);
  };

  const closeModal = () => {
    setModalIsOpen(false);
    setTitle('');
    setDescription('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newAppointment = {
      title,
      start: selectedSlot.start.toISOString(),
      end: selectedSlot.end.toISOString(),
      description,
    };

    const response = await fetch('/api/appointments', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newAppointment),
    });

    if (response.ok) {
      fetchAppointments();
      closeModal();
    }
  };

  return (
    <div>
      <div style={{ height: '600px', margin: '20px 0' }}>
        <Calendar
          localizer={localizer}
          events={events}
          startAccessor="start"
          endAccessor="end"
          style={{ height: '100%' }}
          selectable
          onSelectSlot={handleSelectSlot}
        />
      </div>
      <Modal isOpen={modalIsOpen} onRequestClose={closeModal} contentLabel="Add Appointment">
        <h2>Add Appointment</h2>
        <form onSubmit={handleSubmit}>
          <label>
            Title:
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            Description:
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <button type="submit">Save</button>
          <button onClick={closeModal}>Cancel</button>
        </form>
      </Modal>
    </div>
  );
};

export default MyCalendar;
