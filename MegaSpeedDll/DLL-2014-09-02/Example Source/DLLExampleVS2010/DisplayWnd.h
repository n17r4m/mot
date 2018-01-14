#pragma once


// CDisplayWnd

class CDisplayWnd : public CWnd
{
	DECLARE_DYNAMIC(CDisplayWnd)

public:
	CDisplayWnd();
	virtual ~CDisplayWnd();

	void SetInputData8Bit(int Width, int Height, const unsigned __int8 *InputRawData);
	void SetInputData32Bit(int Width, int Height, const unsigned __int32 *InputData);

protected:
	DECLARE_MESSAGE_MAP()

public:
	afx_msg void OnPaint();
	afx_msg BOOL OnEraseBkgnd(CDC* pDC);
	afx_msg void OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar);
	afx_msg void OnVScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar);
	afx_msg void OnSize(UINT nType, int cx, int cy);

private:
	void UpdateInputSize(int Width, int Height);
	void UpdateScrollBars();
	void ProcessRawData(const unsigned __int8 *RawData);

	unsigned __int32 *DisplayData;

	CBitmap DisplayBmp;

	int ImgWidth;
	int ImgHeight;

	float ScaleW;
	float ScaleH;

	int HScrollPos;
	int VScrollPos;

	int DispWidth;
	int DispHeight;
};