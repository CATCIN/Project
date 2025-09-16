// src/pages/CatFormPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerCatManual } from '../api/catService';
import './CatFormPage.css';

function CatFormPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [note, setNote] = useState('');
  const [preview, setPreview] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const MAX_MB = 15; // 필요시 조정
  const ALLOWED = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];

  const onFileChange = (e) => {
    const f = e.target.files?.[0];
    setError(null);
    setPreview('');
    setFile(null);
    if (!f) return;

    if (!ALLOWED.includes(f.type)) {
      setError('이미지 파일(JPEG/PNG/WEBP)만 업로드 가능합니다.');
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`파일 용량은 최대 ${MAX_MB}MB까지 허용됩니다.`);
      return;
    }

    setFile(f);
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError('사진 파일을 선택해주세요.');
      return;
    }

    try {
      setSubmitting(true);
      const fd = new FormData();
      fd.append('file', file);     
      fd.append('note', note ?? ''); 

      const created = await registerCatManual(fd);
      navigate(`/catcin/cats`);

    } catch (err) {
      setError(err.message || '등록 중 오류가 발생했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="cat-register-manual-page">
      <h1>고양이 수동 등록 (사진 1장)</h1>

      <form className="cat-register-form" onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="file">사진 파일*</label>
          <input
            id="file"
            type="file"
            accept="image/*"
            onChange={onFileChange}
            disabled={submitting}
            required
          />
          {preview && (
            <div className="preview">
              <img src={preview} alt="preview" />
            </div>
          )}
          <small className="hint">허용: JPG/PNG/WEBP, 최대 {MAX_MB}MB</small>
        </div>

        <div className="form-group">
          <label htmlFor="note">메모(선택)</label>
          <textarea
            id="note"
            placeholder="예: 귀 안쪽 상처, 식후 투약 등"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={submitting}
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="actions">
          <button type="submit" className="submit-button" disabled={submitting}>
            {submitting ? '등록 중...' : '등록하기'}
          </button>
          <button
            type="button"
            className="cancel-button"
            disabled={submitting}
            onClick={() => navigate('/catcin/cats')}
          >
            취소
          </button>
        </div>
      </form>
    </div>
  );
}

export default CatFormPage;
