import React, { useState, useEffect } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import Modal from 'react-modal';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import './Calendar.css';

if (process.env.NODE_ENV !== 'test') {
  Modal.setAppElement('#root');
}

const localizer = momentLocalizer(moment);

// Fetch appointments with optional filters
const fetchAppointments = async (filters = {}) => {
  const params = new URLSearchParams();

  // Add filters to query params
  if (filters.status) params.append('status', filters.status);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  // Fetch all pages (or increase per_page for better performance)
  params.append('per_page', '1000');

  const response = await fetch(`/api/appointments?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch appointments');
  }

  const data = await response.json();
  return data.appointments || [];
};

const MyCalendar = () => {
  const navigate = useNavigate();
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Fetch appointments using React Query
  const { data: appointments = [], isLoading, refetch } = useQuery({
    queryKey: ['appointments', statusFilter],
    queryFn: () => fetchAppointments({ status: statusFilter }),
    refetchInterval: 60000, // Refetch every minute
  });

  // Transform appointments to calendar events
  const events = appointments.map(apt => ({
    id: apt.id,
    title: `${apt.title}${apt.patient_name ? ` - ${apt.patient_name}` : ''}`,
    start: new Date(apt.start_time),
    end: new Date(apt.end_time),
    resource: {
      appointmentTypeColor: apt.appointment_type_color || '#2563eb',
      status: apt.status,
      clientName: apt.client_name,
      patientName: apt.patient_name,
      appointmentTypeName: apt.appointment_type_name,
      room: apt.room,
      notes: apt.notes,
    }
  }));

  // Event style getter for color-coding
  const eventStyleGetter = (event) => {
    const color = event.resource?.appointmentTypeColor || '#2563eb';
    const status = event.resource?.status || 'scheduled';

    // Adjust opacity based on status
    let opacity = 1;
    if (status === 'cancelled') opacity = 0.4;
    else if (status === 'completed') opacity = 0.6;
    else if (status === 'no_show') opacity = 0.3;

    return {
      style: {
        backgroundColor: color,
        opacity: opacity,
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        display: 'block',
      }
    };
  };

  // Custom event component to show more details
  const EventComponent = ({ event }) => (
    <div>
      <strong>{event.title}</strong>
      {event.resource?.room && <div style={{ fontSize: '0.85em' }}>Room: {event.resource.room}</div>}
      {event.resource?.status && (
        <div style={{ fontSize: '0.75em', textTransform: 'capitalize' }}>
          {event.resource.status.replace('_', ' ')}
        </div>
      )}
    </div>
  );

  const handleSelectSlot = (slotInfo) => {
    setSelectedSlot(slotInfo);
    setModalIsOpen(true);
  };

  const handleSelectEvent = (event) => {
    // Navigate to appointment detail page
    navigate(`/appointments/${event.id}`);
  };

  const closeModal = () => {
    setModalIsOpen(false);
    setTitle('');
    setDescription('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Note: This is a simplified version. In production, you'd want to:
    // - Select a client and patient
    // - Select an appointment type
    // - Add more fields (status, staff, etc.)
    const newAppointment = {
      title,
      start_time: selectedSlot.start.toISOString(),
      end_time: selectedSlot.end.toISOString(),
      description,
      client_id: 1, // TODO: Replace with actual client selection
      status: 'scheduled',
    };

    const response = await fetch('/api/appointments', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newAppointment),
    });

    if (response.ok) {
      refetch();
      closeModal();
    }
  };

  if (isLoading) {
    return <div style={{ padding: '20px' }}>Loading appointments...</div>;
  }

  return (
    <div>
      {/* Header with New Appointment button */}
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Appointments Calendar</h2>
        <button
          onClick={() => navigate('/appointments/new')}
          style={{
            padding: '10px 20px',
            backgroundColor: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
          }}
        >
          + New Appointment
        </button>
      </div>

      {/* Status filter */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <label htmlFor="status-filter">Filter by status:</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: '5px 10px', borderRadius: '4px', border: '1px solid #ccc' }}
        >
          <option value="">All Statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="confirmed">Confirmed</option>
          <option value="checked_in">Checked In</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="no_show">No Show</option>
        </select>

        {/* Legend */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '15px', fontSize: '0.9em' }}>
          <span>Color = Appointment Type</span>
          <span>Opacity = Status</span>
        </div>
      </div>

      <div style={{ height: '600px', margin: '20px 0' }}>
        <Calendar
          localizer={localizer}
          events={events}
          startAccessor="start"
          endAccessor="end"
          style={{ height: '100%' }}
          selectable
          onSelectSlot={handleSelectSlot}
          onSelectEvent={handleSelectEvent}
          eventPropGetter={eventStyleGetter}
          components={{
            event: EventComponent
          }}
          popup
          views={['month', 'week', 'day']}
          defaultView="week"
        />
      </div>

      <Modal
        isOpen={modalIsOpen}
        onRequestClose={closeModal}
        contentLabel="Add Appointment"
        style={{
          content: {
            top: '50%',
            left: '50%',
            right: 'auto',
            bottom: 'auto',
            marginRight: '-50%',
            transform: 'translate(-50%, -50%)',
            minWidth: '400px',
          }
        }}
      >
        <h2>Add Appointment</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <label style={{ display: 'flex', flexDirection: 'column' }}>
            Title:
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              style={{ marginTop: '5px', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column' }}>
            Description:
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows="4"
              style={{ marginTop: '5px', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </label>
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button type="submit" style={{ flex: 1, padding: '10px', borderRadius: '4px', border: 'none', backgroundColor: '#2563eb', color: 'white', cursor: 'pointer' }}>
              Save
            </button>
            <button type="button" onClick={closeModal} style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc', backgroundColor: 'white', cursor: 'pointer' }}>
              Cancel
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default MyCalendar;
