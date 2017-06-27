classdef DataBag
    % Storage for detection and tracking information
    
    properties
        dbid;
    end
    
    methods
        % Constructor
        function obj = DataBag(db_file)
            if nargin == 1
                if exist(db_file, 'file') == 2;
                    disp('Database file found, opening...');
                else
                    disp('No database file found, creating...');                
                end
                obj.dbid = mksqlite('open', db_file);                
                obj.initTables()                
            end                    
        end
        
        function r = initTables(obj)
            obj.batchBegin()
            if ~ obj.tableExists('frames')
                obj.createFramesTable();
            end
            if ~ obj.tableExists('assoc')
                obj.createAssocTable();
            end
            if ~ obj.tableExists('particles')
                obj.createParticlesTable();
            end
            obj.batchCommit();
        end
        
        function r = tableExists(obj, table)
            r = mksqlite(obj.dbid, 'SELECT count(*) FROM sqlite_master WHERE type="table" AND name=?', table);
            r = r.count___ == 1;
        end
        function r = createFramesTable(obj)
            mksqlite(obj.dbid, 'CREATE TABLE frames (frame INTEGER, bitmap BLOB)');
        end
        function r = createAssocTable(obj)
            mksqlite(obj.dbid, 'CREATE TABLE assoc (frame INTEGER, particle INTEGER, x REAL, y REAL)');
        end
        function r = createParticlesTable(obj)
            mksqlite(obj.dbid, 'CREATE TABLE particles (id INTEGER PRIMARY KEY, area INTEGER, intensity INTEGER, perimeter INTEGER)');
        end
        function r = batchBegin(obj)
            mksqlite(obj.dbid, 'BEGIN');
        end
        function r = batchCommit(obj)
            mksqlite(obj.dbid, 'END TRANSACTION');
        end
        function r = close(obj)
            mksqlite(obj.dbid, 'CLOSE')
        end
        function r = batchInsertParticle(obj, parea, intensity, perimeter, id)
            if ~exist('parea', 'var')
                parea = 1;
            end
            if ~exist('intensity', 'var')
                intensity = 0;
            end
            if ~exist('perimeter', 'var')
                perimeter = 0;
            end
            if ~exist('id', 'var')
                mksqlite('INSERT INTO particles (area, intensity, perimeter) VALUES (?, ?, ?)', parea, intensity, perimeter)
            else
                mksqlite('INSERT INTO particles (id, area, intensity, perimeter) VALUES (?, ?, ?, ?)', id, parea, intensity, perimeter)
            end
        end
        function r = insertParticle(obj, parea, intensity, perimeter, id)
            obj.batchBegin()
            
            if ~exist('parea', 'var')
                parea = 1;
            end
            if ~exist('intensity', 'var')
                intensity = 0;
            end
            if ~exist('perimeter', 'var')
                perimeter = 0;
            end
            if ~exist('id', 'var')
                obj.batchInsertParticle(parea, intensity, perimeter)
            else
                obj.batchInsertParticle(parea, intensity, perimeter, id)
            end            
            
            obj.batchCommit()
        end
        function r = batchInsertAssoc(obj, frame, particle, x, y)
            mksqlite('INSERT INTO assoc (frame, particle, x, y) VALUES (?, ?, ?, ?)', frame, particle, x, y)
        end
        function r = insertAssoc(obj, frame, particle, x, y)
            obj.batchBegin()
            obj.batchInsertAssoc(obj, frame, particle, x, y)
            obj.batchCommit()
        end
        function r = batchInsertFrame(obj, number, bitmap)
            if exist('bitmap', 'var')
                mksqlite('INSERT INTO frames (frame, bitmap) VALUES (?, ?)', number, obj.toPng(bitmap))
            else
                mksqlite('INSERT INTO frames (frame) VALUES (?)', number)
            end
        end
        function r = insertFrame(obj, number, bitmap)
            obj.batchBegin()
            if exist('bitmap', 'var')
                obj.batchInsertFrame(number, bitmap)
            else
                obj.batchInsertFrame(number)
            end
            obj.batchCommit()
        end
        function r = toPng(obj, bitmap)
            % Encode as png
            imwrite(bitmap, 'tmp.png');
            % Read in the binary data
            r = fread(fopen('tmp.png'), '*uint8');
        end
        function r = fromPng(obj, data)
            fwrite(fopen('tmp.png', 'w'), data);
            r = imread('tmp.png');           
        end
        function r = getBitmap(obj, frame_no)
            r = mksqlite('SELECT bitmap FROM frames WHERE frame == (?)', frame_no);
            r = obj.fromPng(r.bitmap);
        end
    end
    
end

