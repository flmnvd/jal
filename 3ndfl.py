import sys, os, re, shutil
import logging, traceback
from datetime import datetime
from PySide2.QtCore import QTranslator, QTimer
from PySide2.QtWidgets import QApplication
from PySide2.QtSql import QSql, QSqlDatabase, QSqlQuery
from jal.widgets.main_window import MainWindow
from jal.db.helpers import db_connection, executeSQL, readSQL, init_and_check_db, LedgerInitError, get_language, update_db_schema
from jal.data_import.statements import ReportType

REPORTDIR = "report"
OUTDIR = "tax"
reportdir = os.path.join(os.getcwd(), REPORTDIR)
outdir = os.path.join(os.getcwd(), OUTDIR)
own_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "jal") + os.sep
sqlfile = os.path.join(own_path, "jal.sqlite")
window:MainWindow = None


def insertSql(sql_text, params = [], forward_only = True):
    query = QSqlQuery(db_connection())
    query.setForwardOnly(forward_only)
    if not query.prepare(sql_text):
        logging.error(f"SQL prep: '{query.lastError().text()}' for query '{sql_text}' with params '{params}'")
        return None
    for param in params:
        query.bindValue(param[0], param[1])
    return query.exec_()

def clean():
    if os.path.isfile(sqlfile):
        os.remove(sqlfile)

def addAllCurrencies():
    currencies = set()
    for fname in os.listdir(reportdir):
        fpath = os.path.join(reportdir,fname)
        broker, account_id, year = fname.split('.')[0].split('-')
        if broker == "ib":
            text = open(fpath, 'r').read()
            currencies.update( {c for c in re.findall('currency="([^"]+)"', text)} )
            currencies.update( {c for c in re.findall('fxCurrency="([^"]+)"', text)} )
    if "EUR" in currencies: currencies.remove("EUR")
    if "RUB" in currencies: currencies.remove("RUB")
    if "USD" in currencies: currencies.remove("USD")
    currencies.add("GBP")
    print(currencies)
    for currency in currencies:
        insertSql("INSERT INTO assets(name, type_id, full_name, src_id) VALUES(:name, 1, :name, 0)",
                  [(":name", currency)])

def addAllBanks():
    currency_query:QSqlQuery = executeSQL("SELECT id,name FROM assets WHERE type_id=1")
    while currency_query.next():
        currency_id = currency_query.value(0)
        currency_name = currency_query.value(1)
        insertSql("INSERT INTO accounts(type_id, name, currency_id, active) VALUES(2,:name,:currency_id,1)",
                  [(":name", "bank"+'-'+currency_name), (":currency_id", currency_id)])

def addFFinBrokerOrganizationPeerAgent():
    insertSql("INSERT INTO agents(name) VALUES('Interactive Brokers')")  # 1
    insertSql("INSERT INTO agents(name) VALUES('Freedom Finance')")      # 2

def addBrokerAccount(name,account_num):
    currency_query:QSqlQuery = executeSQL("SELECT id,name FROM assets WHERE type_id=1")
    while currency_query.next():
        currency_id = currency_query.value(0)
        currency_name = currency_query.value(1)
        peer = '1' if name.startswith('ib') else '2'
        insertSql("INSERT INTO accounts(type_id, name, currency_id, active, number, organization_id) \
                               VALUES(4, :name, :currency_id, 1, :number, :peer)",
                  [(":name", name+'-'+currency_name), (":currency_id", currency_id), (":number", account_num), (":peer", peer)] )

def addAllAccounts():
    accs = set()
    for fname in os.listdir(reportdir):
        fpath = os.path.join(reportdir,fname)
        print(fpath)
        broker,account_id,year = fname.split('.')[0].split('-')
        account_name = broker+'-'+account_id
        if account_name not in accs:
            print(account_name)
            addBrokerAccount(account_name, account_id)
            accs.add(account_name)

def getLoaderType(broker):
    if broker == "ib": return ReportType.IBKR
    if broker == "ff": return ReportType.FFin

def loadReports():
    accs = set()
    #t:\ib-report-xml-cut-parts\2020.xml
    for fname in os.listdir(reportdir):
        fpath = os.path.join(reportdir, fname)
        if os.path.isfile(fpath):
            print(fpath)
            broker,account_id,year = fname.split('.')[0].split('-')
            #account_name = broker+'-'+account_id
            window.statements.loaders[getLoaderType(broker)](fpath)

def loadCurrencyRates():
    timestamp_max = readSQL("SELECT MAX(timestamp) FROM trades")
    timestamp_min = readSQL("SELECT MIN(timestamp) FROM trades")
    window.downloader.UpdateQuotes(timestamp_min, timestamp_max)
    window.onQuotesDownloadCompletion()  #self.download_completed.emit()

def mkOutDir():
    if os.path.isdir(outdir):
        for fname in os.listdir(outdir):
            fpath = os.path.join(outdir, fname)
            if os.path.isfile(fpath) and fname.endswith(".xlsx"):
                os.remove(fpath)
    else:
        os.mkdir(outdir)

def saveTaxReports():
    mkOutDir()
    accounts_query = executeSQL("SELECT id,name,currency_id FROM accounts WHERE type_id=4")
    while accounts_query.next():
        account_id = accounts_query.value(0)
        account_name = accounts_query.value(1)
        currency_id = accounts_query.value(2)
        #currency_name = readSQL("SELECT name FROM assets WHERE id=:id", [(":id",currency_id)])
        try:
            timestamp_max = int(readSQL("SELECT MAX(timestamp) FROM trades WHERE account_id=:id", [(":id",account_id)]))
            timestamp_min = int(readSQL("SELECT MIN(timestamp) FROM trades WHERE account_id=:id", [(":id",account_id)]))
        except: continue
        if timestamp_min==0 or timestamp_max==0: continue
        for year in range(datetime.fromtimestamp(timestamp_min).year, datetime.fromtimestamp(timestamp_max).year+1):
            fpath = os.path.join(outdir, account_name+'-'+str(year)+'.xlsx')
            window.taxes.use_settlement = True
            window.taxes.save2file(fpath, year, account_id)

def doThings():
    addFFinBrokerOrganizationPeerAgent()
    addAllCurrencies()
    addAllBanks()
    addAllAccounts()
    loadReports()
    window.onStatementLoaded()  #self.load_completed.emit()
    loadCurrencyRates()
    saveTaxReports()


#-----------------------------------------------------------------------------------------------------------------------
def exception_logger(exctype, value, tb):
    info = traceback.format_exception(exctype, value, tb)
    logging.fatal(f"EXCEPTION: {info}")
    sys.__excepthook__(exctype, value, tb)


#-----------------------------------------------------------------------------------------------------------------------
def main():
    sys.excepthook = exception_logger
    os.environ['QT_MAC_WANTS_LAYER'] = '1'    # Workaround for https://bugreports.qt.io/browse/QTBUG-87014

    clean()

    #own_path = os.path.dirname(os.path.realpath(__file__)) + os.sep
    error = init_and_check_db(own_path)

    if error.code == LedgerInitError.EmptyDbInitialized:  # If DB was just created from SQL - initialize it again
        error = init_and_check_db(own_path)

    app = QApplication([])
    language = get_language()
    translator = QTranslator(app)
    language_file = own_path + "languages" + os.sep + language + '.qm'
    translator.load(language_file)
    app.installTranslator(translator)

    if error.code == LedgerInitError.OutdatedDbSchema:
        error = update_db_schema(own_path)
        if error.code == LedgerInitError.DbInitSuccess:
            db, error = init_and_check_db(own_path)

    global window
    if error.code != LedgerInitError.DbInitSuccess:
        window = QMessageBox()
        window.setAttribute(Qt.WA_DeleteOnClose)
        window.setWindowTitle("JAL: Start-up aborted")
        window.setIcon(QMessageBox.Critical)
        window.setText(error.message)
        window.setInformativeText(error.details)
    else:
        window = MainWindow(own_path, language)
        window.activateLoggingTab()
        QTimer.singleShot(0,doThings)
    window.show()

    app.exec_()
    app.removeTranslator(translator)

if __name__ == "__main__":
    main()
