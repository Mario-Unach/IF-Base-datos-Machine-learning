-- ====================================================================
-- MIGRACION POR PARTES - CC_Client
-- Proposito: apoyar la interaccion desde Streamlit con operaciones de
-- consultar, nuevo (migrar por lote), eliminar y guardar.
-- ====================================================================

USE CC_Client;
GO

SET NOCOUNT ON;
GO

-- ====================================================================
-- 1. RESUMEN GENERAL PARA EL BOTON CONSULTAR
-- ====================================================================
CREATE OR ALTER VIEW dbo.vw_resumen_migracion
AS
SELECT
    (SELECT COUNT(*) FROM dbo.staging_credit_cards) AS total_staging,
    (SELECT COUNT(*) FROM dbo.dim_cliente) AS total_clientes,
    (SELECT COUNT(*) FROM dbo.riesgo_crediticio) AS total_riesgo,
    (SELECT COUNT(*) FROM dbo.historial_pagos) AS total_historial,
    (SELECT COUNT(*) FROM dbo.staging_credit_cards) AS pendientes_por_migrar;
GO

-- ====================================================================
-- 2. VER EL PROXIMO LOTE DE STAGING SIN MODIFICAR DATOS
--    Sirve para el boton consultar o para mostrar vista previa.
-- ====================================================================
CREATE OR ALTER PROCEDURE dbo.sp_ver_lote_staging
    @CantidadRegistros INT = 10
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP (@CantidadRegistros)
        ID,
        LIMIT_BAL,
        SEX,
        EDUCATION,
        MARRIAGE,
        AGE,
        PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6,
        BILL_AMT1, BILL_AMT2, BILL_AMT3, BILL_AMT4, BILL_AMT5, BILL_AMT6,
        PAY_AMT1, PAY_AMT2, PAY_AMT3, PAY_AMT4, PAY_AMT5, PAY_AMT6,
        default_payment_next_month
    FROM dbo.staging_credit_cards
    ORDER BY ID;
END;
GO

-- ====================================================================
-- 3. MIGRACION POR PARTES
--    Inserta N registros desde staging hacia las tablas finales.
--    Ademas elimina del staging los registros ya migrados para evitar
--    duplicados en la siguiente ejecucion.
-- ====================================================================
CREATE OR ALTER PROCEDURE dbo.sp_migrar_lote_credit_cards
    @CantidadRegistros INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @CantidadRegistros IS NULL OR @CantidadRegistros <= 0
    BEGIN
        RAISERROR('La cantidad de registros debe ser mayor que cero.', 16, 1);
        RETURN;
    END;

    IF NOT EXISTS (SELECT 1 FROM dbo.staging_credit_cards)
    BEGIN
        RAISERROR('No hay registros disponibles en staging_credit_cards.', 16, 1);
        RETURN;
    END;

    CREATE TABLE #lote_staging (
        ID INT,
        LIMIT_BAL DECIMAL(18,2),
        SEX INT,
        EDUCATION INT,
        MARRIAGE INT,
        AGE INT,
        PAY_0 INT, PAY_2 INT, PAY_3 INT, PAY_4 INT, PAY_5 INT, PAY_6 INT,
        BILL_AMT1 DECIMAL(18,2), BILL_AMT2 DECIMAL(18,2), BILL_AMT3 DECIMAL(18,2),
        BILL_AMT4 DECIMAL(18,2), BILL_AMT5 DECIMAL(18,2), BILL_AMT6 DECIMAL(18,2),
        PAY_AMT1 DECIMAL(18,2), PAY_AMT2 DECIMAL(18,2), PAY_AMT3 DECIMAL(18,2),
        PAY_AMT4 DECIMAL(18,2), PAY_AMT5 DECIMAL(18,2), PAY_AMT6 DECIMAL(18,2),
        default_payment_next_month BIT
    );

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO #lote_staging
        SELECT TOP (@CantidadRegistros)
            ID,
            LIMIT_BAL,
            SEX,
            EDUCATION,
            MARRIAGE,
            AGE,
            PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6,
            BILL_AMT1, BILL_AMT2, BILL_AMT3, BILL_AMT4, BILL_AMT5, BILL_AMT6,
            PAY_AMT1, PAY_AMT2, PAY_AMT3, PAY_AMT4, PAY_AMT5, PAY_AMT6,
            default_payment_next_month
        FROM dbo.staging_credit_cards
        ORDER BY ID;

        INSERT INTO dbo.dim_cliente (id_cliente, id_sexo, id_educacion, id_estado_civil, edad, limite_credito)
        SELECT
            ID,
            SEX,
            EDUCATION,
            MARRIAGE,
            AGE,
            LIMIT_BAL
        FROM #lote_staging b
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.dim_cliente dc
            WHERE dc.id_cliente = b.ID
        );

        INSERT INTO dbo.riesgo_crediticio (id_cliente, incumplimiento_proximo_mes)
        SELECT
            ID,
            default_payment_next_month
        FROM #lote_staging b
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.riesgo_crediticio rc
            WHERE rc.id_cliente = b.ID
        );

        INSERT INTO dbo.historial_pagos (
            id_cliente,
            id_mes,
            id_estatus_pago,
            monto_estado_cuenta,
            monto_pago_anterior
        )
        SELECT
            b.ID,
            meses.id_mes,
            meses.id_estatus_pago,
            meses.monto_estado_cuenta,
            meses.monto_pago_anterior
        FROM #lote_staging b
        CROSS APPLY (
            VALUES
                (1, b.PAY_0, b.BILL_AMT1, b.PAY_AMT1),
                (2, b.PAY_2, b.BILL_AMT2, b.PAY_AMT2),
                (3, b.PAY_3, b.BILL_AMT3, b.PAY_AMT3),
                (4, b.PAY_4, b.BILL_AMT4, b.PAY_AMT4),
                (5, b.PAY_5, b.BILL_AMT5, b.PAY_AMT5),
                (6, b.PAY_6, b.BILL_AMT6, b.PAY_AMT6)
        ) AS meses(id_mes, id_estatus_pago, monto_estado_cuenta, monto_pago_anterior)
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.historial_pagos hp
            WHERE hp.id_cliente = b.ID
              AND hp.id_mes = meses.id_mes
              AND hp.id_estatus_pago = meses.id_estatus_pago
        );

        DELETE s
        FROM dbo.staging_credit_cards s
        INNER JOIN #lote_staging b ON s.ID = b.ID;

        COMMIT TRANSACTION;

        SELECT
            @CantidadRegistros AS registros_solicitados,
            (SELECT COUNT(*) FROM #lote_staging) AS registros_migrados,
            (SELECT COUNT(*) FROM dbo.staging_credit_cards) AS registros_restantes_staging;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @Mensaje NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @Severidad INT = ERROR_SEVERITY();
        DECLARE @Estado INT = ERROR_STATE();

        RAISERROR(@Mensaje, @Severidad, @Estado);
    END CATCH
END;
GO

-- ====================================================================
-- 3B. ALIAS PARA EL BOTON GUARDAR
--    Usa la misma migracion por lotes, pero con un nombre mas didactico.
-- ====================================================================
CREATE OR ALTER PROCEDURE dbo.sp_guardar_lote_credit_cards
    @CantidadRegistros INT
AS
BEGIN
    EXEC dbo.sp_migrar_lote_credit_cards @CantidadRegistros = @CantidadRegistros;
END;
GO

-- ====================================================================
-- 4. ELIMINAR REGISTROS DEL STAGING POR LOTE
--    Util para el boton eliminar cuando quieras quitar registros antes
--    de migrarlos.
-- ====================================================================
CREATE OR ALTER PROCEDURE dbo.sp_eliminar_lote_staging
    @CantidadRegistros INT
AS
BEGIN
    SET NOCOUNT ON;

    IF @CantidadRegistros IS NULL OR @CantidadRegistros <= 0
    BEGIN
        RAISERROR('La cantidad de registros debe ser mayor que cero.', 16, 1);
        RETURN;
    END;

    DELETE TOP (@CantidadRegistros)
    FROM dbo.staging_credit_cards
    WHERE ID IN (
        SELECT TOP (@CantidadRegistros) ID
        FROM dbo.staging_credit_cards
        ORDER BY ID
    );

    SELECT
        @CantidadRegistros AS registros_solicitados,
        @@ROWCOUNT AS registros_eliminados,
        (SELECT COUNT(*) FROM dbo.staging_credit_cards) AS registros_restantes_staging;
END;
GO

-- ====================================================================
-- 5. ELIMINAR UN CLIENTE YA MIGRADO
--    Borra primero las tablas hijas y despues el cliente.
-- ====================================================================
CREATE OR ALTER PROCEDURE dbo.sp_eliminar_cliente_migrado
    @IdCliente INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE FROM dbo.historial_pagos
        WHERE id_cliente = @IdCliente;

        DELETE FROM dbo.riesgo_crediticio
        WHERE id_cliente = @IdCliente;

        DELETE FROM dbo.dim_cliente
        WHERE id_cliente = @IdCliente;

        COMMIT TRANSACTION;

        SELECT @IdCliente AS id_cliente_eliminado;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @Mensaje NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @Severidad INT = ERROR_SEVERITY();
        DECLARE @Estado INT = ERROR_STATE();

        RAISERROR(@Mensaje, @Severidad, @Estado);
    END CATCH
END;
GO

-- ====================================================================
-- 6. EJEMPLOS DE USO PARA STREAMLIT
-- ====================================================================
-- Consultar resumen:
-- SELECT * FROM dbo.vw_resumen_migracion;
-- EXEC dbo.sp_ver_lote_staging @CantidadRegistros = 10;
-- EXEC dbo.sp_migrar_lote_credit_cards @CantidadRegistros = 25;
-- EXEC dbo.sp_eliminar_lote_staging @CantidadRegistros = 5;
-- EXEC dbo.sp_eliminar_cliente_migrado @IdCliente = 52;
