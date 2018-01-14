
// DLLExampleVS2010.h : main header file for the PROJECT_NAME application
//

#pragma once

#ifndef __AFXWIN_H__
	#error "include 'stdafx.h' before including this file for PCH"
#endif

#include "resource.h"		// main symbols


// CDLLExampleVS2010App:
// See DLLExampleVS2010.cpp for the implementation of this class
//

class CDLLExampleVS2010App : public CWinApp
{
public:
	CDLLExampleVS2010App();

// Overrides
public:
	virtual BOOL InitInstance();

// Implementation

	DECLARE_MESSAGE_MAP()
};

extern CDLLExampleVS2010App theApp;