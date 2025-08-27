import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createMedicine } from '../api/medicineService';
import './MedicineFormPage.css';

function MedicineFormPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [image, setImage] = useState(null);
  const [category, setCategory] = useState('');
  const [interval, setInterval] = useState(0);
  const [expiresDate, setExpiresDate] = useState(''); // "YYYY-MM-DD"
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const categoryOptions = [
    { value: '항생제', label: '항생제' },
    { value: '진통제', label: '진통제' },
    { value: '비타민', label: '비타민' },
    { value: '영양제', label: '영양제' },
  ];

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // 필수값 체크
    if (!name || !category || !interval || !expiresDate) {
      setError('필수 항목을 모두 입력해주세요.');
      setSubmitting(false);
      return;
    }

    // 1) FormData 생성
    const formData = new FormData();
    formData.append('name', name);
    formData.append('category', category);
    formData.append('interval', interval.toString());
    formData.append('expires_date', expiresDate); // "YYYY-MM-DD" 형식
    formData.append('note', note);
    if (image) {
      formData.append('image', image);
    }

    try {
      // 2) FormData를 createMedicine로 넘긴다
      await createMedicine(formData);
      navigate('/medicines');
    } catch (err) {
      setError(err.message || 'Failed to create medicine');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="medicine-form-page">
      <h1>Add New Medicine</h1>
      <form onSubmit={handleSubmit} className="medicine-form">
        {/* Name* */}
        <div className="form-group">
          <label htmlFor="name">Name*</label>
          <input
            id="name"
            type="text"
            value={name}
            required
            onChange={(e) => setName(e.target.value)}
            placeholder="예: Panacur"
          />
        </div>

        {/* Image */}
        <div className="form-group">
          <label htmlFor="image">Image</label>
          <input
            id="image"
            type="file"
            accept="image/*"
            onChange={(e) => setImage(e.target.files[0])}
          />
        </div>

        {/* Category* */}
        <div className="form-group">
          <label htmlFor="category">Category*</label>
          <select
            id="category"
            value={category}
            required
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="" disabled>
              -- Select Category --
            </option>
            {categoryOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Interval (days)* */}
        <div className="form-group">
          <label htmlFor="interval">Interval (days)*</label>
          <input
            id="interval"
            type="number"
            min="0"
            value={interval}
            required
            onChange={(e) => setInterval(parseInt(e.target.value, 10) || 0)}
          />
        </div>

        {/* Expires Date (date) */}
        <div className="form-group">
          <label htmlFor="expiresDate">Expires Date</label>
          <input
            id="expiresDate"
            type="date"
            value={expiresDate}
            onChange={(e) => setExpiresDate(e.target.value)}
          />
        </div>

        {/* Note */}
        <div className="form-group">
          <label htmlFor="note">Note</label>
          <textarea
            id="note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="예: 식전 투약"
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button type="submit" className="submit-button" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Create Medicine'}
        </button>
        <button
          type="button"
          className="cancel-button"
          onClick={() => navigate('/catcin/medicines')}
          disabled={submitting}
        >
          Cancel
        </button>
      </form>
    </div>
  );
}

export default MedicineFormPage;