------------------VISTAS ESTRUCTURADAS -----------------------------
--1 VISTA PARA DATASET PLANO
CREATE OR ALTER VIEW vw_ml_dataset AS
WITH HistorialPivot AS (
    SELECT 
        id_cliente,
        MAX(CASE WHEN id_mes = 1 THEN id_estatus_pago END) AS PAY_0,
        MAX(CASE WHEN id_mes = 2 THEN id_estatus_pago END) AS PAY_2,
        MAX(CASE WHEN id_mes = 3 THEN id_estatus_pago END) AS PAY_3,
        MAX(CASE WHEN id_mes = 4 THEN id_estatus_pago END) AS PAY_4,
        MAX(CASE WHEN id_mes = 5 THEN id_estatus_pago END) AS PAY_5,
        MAX(CASE WHEN id_mes = 6 THEN id_estatus_pago END) AS PAY_6,
        MAX(CASE WHEN id_mes = 1 THEN monto_estado_cuenta END) AS BILL_AMT1,
        MAX(CASE WHEN id_mes = 2 THEN monto_estado_cuenta END) AS BILL_AMT2,
        MAX(CASE WHEN id_mes = 3 THEN monto_estado_cuenta END) AS BILL_AMT3,
        MAX(CASE WHEN id_mes = 4 THEN monto_estado_cuenta END) AS BILL_AMT4,
        MAX(CASE WHEN id_mes = 5 THEN monto_estado_cuenta END) AS BILL_AMT5,
        MAX(CASE WHEN id_mes = 6 THEN monto_estado_cuenta END) AS BILL_AMT6,
        MAX(CASE WHEN id_mes = 1 THEN monto_pago_anterior END) AS PAY_AMT1,
        MAX(CASE WHEN id_mes = 2 THEN monto_pago_anterior END) AS PAY_AMT2,
        MAX(CASE WHEN id_mes = 3 THEN monto_pago_anterior END) AS PAY_AMT3,
        MAX(CASE WHEN id_mes = 4 THEN monto_pago_anterior END) AS PAY_AMT4,
        MAX(CASE WHEN id_mes = 5 THEN monto_pago_anterior END) AS PAY_AMT5,
        MAX(CASE WHEN id_mes = 6 THEN monto_pago_anterior END) AS PAY_AMT6
    FROM historial_pagos
    GROUP BY id_cliente
)
SELECT 
    c.id_cliente,
    c.id_sexo,
    c.id_educacion,
    c.id_estado_civil,
    c.edad,
    c.limite_credito,
    h.PAY_0,
    h.PAY_2,
    h.PAY_3,
    h.PAY_4,
    h.PAY_5,
    h.PAY_6,
    h.BILL_AMT1,
    h.BILL_AMT2,
    h.BILL_AMT3,
    h.BILL_AMT4,
    h.BILL_AMT5,
    h.BILL_AMT6,
    h.PAY_AMT1,
    h.PAY_AMT2,
    h.PAY_AMT3,
    h.PAY_AMT4,
    h.PAY_AMT5,
    h.PAY_AMT6,
    r.incumplimiento_proximo_mes AS target
FROM dim_cliente c
INNER JOIN HistorialPivot h ON c.id_cliente = h.id_cliente
INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente;
GO

-- Vista total de los registros
--SELECT *
--FROM vw_ml_dataset
--ORDER BY id_cliente;

-- VISTA PARA ANÁLISIS EXPLORATORIO CON DESCRIPCIONES

CREATE OR ALTER VIEW vw_cliente_detallado AS
SELECT 
    c.id_cliente,
    s.descripcion_sexo AS sexo,
    e.nivel_educativo AS educacion,
    ec.descripcion_estado_civil AS estado_civil,
    c.edad,
    c.limite_credito,
    r.incumplimiento_proximo_mes AS target
FROM dim_cliente c
INNER JOIN dim_sexo s ON c.id_sexo = s.id_sexo
INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
INNER JOIN dim_estado_civil ec ON c.id_estado_civil = ec.id_estado_civil
INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente;
GO
-- comprobacion de las vistas con sus descripciones
--SELECT TOP 50 *
--FROM vw_cliente_detallado
--ORDER BY id_cliente;

-- Agregamos índice en historial_pagos por id_cliente e id_mes (para acelerar el pivot).
CREATE NONCLUSTERED INDEX idx_historial_cliente_mes ON historial_pagos (id_cliente, id_mes) 
INCLUDE (id_estatus_pago, monto_estado_cuenta, monto_pago_anterior);
GO
-- Índice en riesgo_crediticio para optimizar consultas por la variable objetivo (target)
CREATE NONCLUSTERED INDEX idx_riesgo_target 
ON riesgo_crediticio (incumplimiento_proximo_mes) 
INCLUDE (id_cliente);
GO

-- TABLA DE AUDITORÍA
CREATE TABLE auditoria_cambios (
    id_auditoria BIGINT IDENTITY(1,1) PRIMARY KEY,
    tabla_afectada VARCHAR(100) NOT NULL,
    operacion CHAR(1) NOT NULL, -- 'I', 'U', 'D'
    id_registro_afectado INT NOT NULL, 
    usuario VARCHAR(100) NOT NULL DEFAULT SUSER_NAME(),
    fecha_cambio DATETIME NOT NULL DEFAULT GETDATE(),
    datos_antes NVARCHAR(MAX) NULL,  -- para UPDATE o DELETE
    datos_despues NVARCHAR(MAX) NULL -- para INSERT o UPDATE
);
GO

CREATE OR ALTER TRIGGER trg_Auditoria_Riesgo
ON riesgo_crediticio
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- Registrar Inserciones
    IF EXISTS (SELECT * FROM inserted) AND NOT EXISTS (SELECT * FROM deleted)
    BEGIN
        INSERT INTO auditoria_cambios (tabla_afectada, operacion, id_registro_afectado, datos_despues)
        SELECT 'riesgo_crediticio', 'I', id_cliente, 
               CONVERT(NVARCHAR(MAX), incumplimiento_proximo_mes)
        FROM inserted;
    END

    -- Registrar Actualizaciones
    IF EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
    BEGIN
        INSERT INTO auditoria_cambios (tabla_afectada, operacion, id_registro_afectado, datos_antes, datos_despues)
        SELECT 'riesgo_crediticio', 'U', i.id_cliente,
               CONVERT(NVARCHAR(MAX), d.incumplimiento_proximo_mes),
               CONVERT(NVARCHAR(MAX), i.incumplimiento_proximo_mes)
        FROM inserted i
        JOIN deleted d ON i.id_cliente = d.id_cliente;
    END

    -- Registrar Eliminaciones
    IF EXISTS (SELECT * FROM deleted) AND NOT EXISTS (SELECT * FROM inserted)
    BEGIN
        INSERT INTO auditoria_cambios (tabla_afectada, operacion, id_registro_afectado, datos_antes)
        SELECT 'riesgo_crediticio', 'D', id_cliente, 
               CONVERT(NVARCHAR(MAX), incumplimiento_proximo_mes)
        FROM deleted;
    END
END;
GO

------------ROLES Y USUARIOS-------------------
USE CC_Client;
GO

-- Crear roles
CREATE ROLE rol_analista;
CREATE ROLE rol_admin;

-- Asignar permisos al rol_analista (solo lectura)
GRANT SELECT ON vista_cliente_ml TO rol_analista;
GRANT SELECT ON vista_historial_cliente TO rol_analista;

GRANT SELECT ON dim_cliente TO rol_analista;
GRANT SELECT ON dim_sexo TO rol_analista;
GRANT SELECT ON dim_educacion TO rol_analista;
GRANT SELECT ON dim_estado_civil TO rol_analista;
GRANT SELECT ON dim_tiempo_mes TO rol_analista;
GRANT SELECT ON dim_estatus_pago TO rol_analista;
GRANT SELECT ON historial_pagos TO rol_analista;
GRANT SELECT ON riesgo_crediticio TO rol_analista;
-- No dar INSERT/UPDATE/DELETE

-- Permisos al rol_admin (todos los privilegios en la base de datos)
GRANT CONTROL ON DATABASE::CC_Client TO rol_admin;

-- Crear logins con contraseña (nivel servidor)
CREATE LOGIN analista WITH PASSWORD = 'ContraseñaSegura123*';
CREATE LOGIN admin WITH PASSWORD = 'ContraseñaSegura456*';

-- Crear usuarios en la base vinculados a los logins
CREATE USER analista FOR LOGIN analista;
CREATE USER admin FOR LOGIN admin;

-- Asignar roles a los usuarios
ALTER ROLE rol_analista ADD MEMBER analista;
ALTER ROLE rol_admin ADD MEMBER admin;
GO


---Estrategia de Backups y Restauración--------
-- Backup completo de la base de datos CC_Client
BACKUP DATABASE CC_Client
TO DISK = 'C:\Backup\CC_Client_Full.bak'
WITH FORMAT, INIT, NAME = 'Full Backup CC_Client';
GO

-- Backup diferencial
BACKUP DATABASE CC_Client
TO DISK = 'C:\Backup\CC_Client_Diff.bak'
WITH DIFFERENTIAL, NAME = 'Differential Backup CC_Client';
GO

-- Backup de log transaccional 
BACKUP LOG CC_Client
TO DISK = 'C:\Backup\CC_Client_Log.trn'
WITH NAME = 'Log Backup CC_Client';
GO

-- Restauracion 
-- Restaurar FULL
RESTORE DATABASE CC_Client
FROM DISK = 'C:\Backup\CC_Client_Full.bak'
WITH NORECOVERY; -- Dejar en estado de restauración para aplicar logs

-- Restaurar DIFF (si existe)
RESTORE DATABASE CC_Client
FROM DISK = 'C:\Backup\CC_Client_Diff.bak'
WITH NORECOVERY;

-- Restaurar logs (uno o varios)
RESTORE LOG CC_Client
FROM DISK = 'C:\Backup\CC_Client_Log.trn'
WITH RECOVERY; -- Último log con RECOVERY para dejar la BD operativa