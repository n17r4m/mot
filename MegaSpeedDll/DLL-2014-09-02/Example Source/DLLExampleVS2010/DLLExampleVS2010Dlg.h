
// DLLExampleVS2010Dlg.h : header file
//

#pragma once


// CDLLExampleVS2010Dlg dialog
class CDLLExampleVS2010Dlg : public CDialogEx
{
// Construction
public:
	CDLLExampleVS2010Dlg(CWnd* pParent = NULL);	// standard constructor

// Dialog Data
	enum { IDD = IDD_DLLEXAMPLEVS2010_DIALOG };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support


// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	virtual BOOL OnInitDialog();
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()
public:
//	CListBox m_MsgList;
	afx_msg void OnClickedBtnCapture();
	afx_msg void OnClickedBtnConnect();
	afx_msg void OnClickedBtnDownload();
	afx_msg void OnTimer(UINT_PTR nIDEvent);
	afx_msg void OnDestroy();
	afx_msg void OnClickedBtnPrepost();
};
