import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createMedicine } from '../api/medicineService';
import './MedicineFormPage.css';

function MedicineFormPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [image, setImage] = useState(null); 
  const [preview, setPreview] = useState(''); 
  const [category, setCategory] = useState('');
  const [interval, setInterval] = useState(0);
  const [expiresDate, setExpiresDate] = useState(''); 
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const MAX_MB = 15;
  const ALLOWED = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];

  const categoryOptions = [
    { value: 'antibiotic', label: '항생제' },
    { value: 'painkiller', label: '진통제' },
    { value: 'vitamin', label: '비타민' },
    { value: 'nutritional', label: '영양제' },
    { value: 'anthelmintic', label: '구충제' },
  ];

  const handleImageChange = (e) => {
    const f = e.target.files?.[0];
    setError(null);
    setPreview('');
    setImage(null);
    if (!f) return;

    if (!ALLOWED.includes(f.type)) {
      setError('이미지 파일(JPEG/PNG/WEBP)만 업로드 가능합니다.');
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`파일 용량은 최대 ${MAX_MB}MB까지 허용됩니다.`);
      return;
    }

    setImage(f);
    const url = URL.createObjectURL(f);
    setPreview(url); 
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    if (!name || !category || !interval || !expiresDate) {
      setError('필수 항목을 모두 입력해주세요.');
      setSubmitting(false);
      return;
    }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('category', category);
    formData.append('interval', interval.toString());
    formData.append('expires_date', expiresDate);
    formData.append('note', note);
    if (image) { 
      formData.append('image', image);
    }

    try {
      await createMedicine(formData);
      navigate('/catcin/medicines');
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

        <div className="form-group">
          <label htmlFor="image">Image</label>
          <input
            id="image"
            type="file"
            accept="image/*"
            onChange={handleImageChange} 
          />
          {preview && (
            <div className="preview">
              <img src={preview} alt="Preview" />
            </div>
          )}
          <small className="hint">허용: JPG/PNG/WEBP, 최대 {MAX_MB}MB</small>
        </div>

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

        <div className="form-group">
          <label htmlFor="expiresDate">Expires Date*</label> 
          <input
            id="expiresDate"
            type="date"
            value={expiresDate}
            required 
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