from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QLabel, QDateTimeEdit, QPushButton, QTableView, QLineEdit, QHeaderView
from PySide2.QtGui import QDoubleValidator
from PySide2.QtSql import QSqlTableModel, QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate
from jal.constants import Setup
from jal.ui_custom.helpers import g_tr
from jal.ui_custom.abstract_operation_details import AbstractOperationDetails
from jal.ui_custom.reference_selector import AccountSelector, PeerSelector, CategorySelector, TagSelector
from jal.widgets.mapper_delegate import MapperDelegate


class IncomeSpendingWidget(AbstractOperationDetails):
    def __init__(self, parent=None):
        AbstractOperationDetails.__init__(self, parent)
        self.details_model = None
        self.category_delegate = CategoryDelegate()
        self.tag_delegate = TagDelegate()
        self.float_delegate = FloatDelegate()

        self.date_label = QLabel(self)
        self.details_label = QLabel(self)
        self.account_label = QLabel(self)
        self.peer_label = QLabel(self)

        self.main_label.setText(g_tr("IncomeSpendingWidget", "Income / Spending"))
        self.date_label.setText(g_tr("IncomeSpendingWidget", "Date/Time"))
        self.details_label.setText(g_tr("IncomeSpendingWidget", "Details"))
        self.account_label.setText(g_tr("IncomeSpendingWidget", "Account"))
        self.peer_label.setText(g_tr("IncomeSpendingWidget", "Peer"))

        self.timestamp_editor = QDateTimeEdit(self)
        self.timestamp_editor.setCalendarPopup(True)
        self.timestamp_editor.setTimeSpec(Qt.UTC)
        self.timestamp_editor.setFixedWidth(self.timestamp_editor.fontMetrics().width("00/00/0000 00:00:00") * 1.25)
        self.timestamp_editor.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.account_widget = AccountSelector(self)
        self.peer_widget = PeerSelector(self)
        self.add_button = QPushButton(self)
        self.add_button.setText(" +️ ")
        self.add_button.setFont(self.bold_font)
        self.add_button.setFixedWidth(self.add_button.fontMetrics().width("XXX"))
        self.del_button = QPushButton(self)
        self.del_button.setText(" — ️")
        self.del_button.setFont(self.bold_font)
        self.del_button.setFixedWidth(self.del_button.fontMetrics().width("XXX"))
        self.copy_button = QPushButton(self)
        self.copy_button.setText(" >> ️")
        self.copy_button.setFont(self.bold_font)
        self.copy_button.setFixedWidth(self.copy_button.fontMetrics().width("XXX"))
        self.details_table = QTableView(self)
        self.details_table.horizontalHeader().setFont(self.bold_font)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.verticalHeader().setMinimumSectionSize(20)
        self.details_table.verticalHeader().setDefaultSectionSize(20)

        self.layout.addWidget(self.date_label, 1, 0, 1, 1, Qt.AlignLeft)
        self.layout.addWidget(self.details_label, 2, 0, 1, 1, Qt.AlignLeft)

        self.layout.addWidget(self.timestamp_editor, 1, 1, 1, 4)
        self.layout.addWidget(self.add_button, 2, 1, 1, 1)
        self.layout.addWidget(self.copy_button, 2, 2, 1, 1)
        self.layout.addWidget(self.del_button, 2, 3, 1, 1)

        self.layout.addWidget(self.account_label, 1, 5, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.peer_label, 2, 5, 1, 1, Qt.AlignRight)

        self.layout.addWidget(self.account_widget, 1, 6, 1, 1)
        self.layout.addWidget(self.peer_widget, 2, 6, 1, 1)

        self.layout.addWidget(self.commit_button, 0, 8, 1, 1)
        self.layout.addWidget(self.revert_button, 0, 9, 1, 1)

        self.layout.addWidget(self.details_table, 4, 0, 1, 10)
        self.layout.addItem(self.horizontalSpacer, 1, 7, 1, 1)

        self.add_button.clicked.connect(self.addChild)
        self.del_button.clicked.connect(self.delChild)

    def init_db(self, db):
        super().init_db(db, "actions")
        self.mapper.setItemDelegate(MapperDelegate(self.mapper))

        self.details_model = DetailsModel(self.details_table, db)
        self.details_model.setTable("action_details")
        self.details_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.details_model.setJoinMode(QSqlRelationalTableModel.LeftJoin)  # to work correctly with NULL values
        self.details_model.setRelation(self.details_model.fieldIndex("category_id"),
                                       QSqlRelation("categories", "id", "name"))
        self.details_model.setRelation(self.details_model.fieldIndex("tag_id"),
                                       QSqlRelation("tags", "id", "tag"))
        self.details_table.setModel(self.details_model)

        self.account_widget.init_db(db)
        self.peer_widget.init_db(db)
        self.account_widget.changed.connect(self.mapper.submit)
        self.peer_widget.changed.connect(self.mapper.submit)

        self.mapper.addMapping(self.timestamp_editor, self.model.fieldIndex("timestamp"))
        self.mapper.addMapping(self.account_widget, self.model.fieldIndex("account_id"))
        self.mapper.addMapping(self.peer_widget, self.model.fieldIndex("peer_id"))

        self.details_table.setItemDelegateForColumn(2, self.category_delegate)
        self.details_table.setItemDelegateForColumn(3, self.tag_delegate)
        self.details_table.setItemDelegateForColumn(4, self.float_delegate)
        self.details_table.setItemDelegateForColumn(5, self.float_delegate)

        self.model.select()
        self.details_model.select()
        self.details_model.configureView()

    def setId(self, id):
        super().setId(id)
        self.details_model.setFilter(f"action_details.pid = {id}")

    @Slot()
    def addChild(self):
        new_record = self.details_model.record()
        self.details_model.insertRecord(-1, new_record)

    @Slot()
    def delChild(self):
        idx = self.details_table.selectionModel().selection().indexes()
        selected_row = idx[0].row()
        self.details_model.removeRow(selected_row)
        self.details_table.setRowHidden(selected_row, True)


class DetailsModel(QSqlRelationalTableModel):
    def __init__(self, parent_view, db):
        self._columns = ["id",
                         "pid",
                         g_tr('DetailsModel', "Category"),
                         g_tr('DetailsModel', "Tag"),
                         g_tr('DetailsModel', "Amount"),
                         g_tr('DetailsModel', "Amount *"),
                         g_tr('DetailsModel', "Note")]
        super().__init__(parent=parent_view, db=db)
        self._view = parent_view

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section]
        return None

    def configureView(self):
        self._view.setColumnHidden(0, True)
        self._view.setColumnHidden(1, True)
        self._view.setColumnWidth(2, 200)
        self._view.setColumnWidth(3, 200)
        self._view.setColumnWidth(4, 100)
        self._view.setColumnWidth(5, 100)
        self._view.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self._view.horizontalHeader().moveSection(6, 0)

# -----------------------------------------------------------------------------------------------------------------------
# Delegate to display category editor
class CategoryDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        QSqlRelationalDelegate.__init__(self, parent)

    def createEditor(self, aParent, option, index):
        category_selector = CategorySelector(aParent)
        category_selector.init_db(index.model().database())
        return category_selector

    def setModelData(self, editor, model, index):
        model.setData(index, editor.selected_id)

# -----------------------------------------------------------------------------------------------------------------------
# Delegate to display tag editor
class TagDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        QSqlRelationalDelegate.__init__(self, parent)

    def createEditor(self, aParent, option, index):
        tag_selector = TagSelector(aParent)
        tag_selector.init_db(index.model().database())
        return tag_selector

    def setModelData(self, editor, model, index):
        model.setData(index, editor.selected_id)


# -----------------------------------------------------------------------------------------------------------------------
# Delegate for nice float numbers formatting
class FloatDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        QSqlRelationalDelegate.__init__(self, parent)

    def formatFloatLong(self, value):
        if abs(value - round(value, 2)) >= Setup.CALC_TOLERANCE:
            text = str(value)
        else:
            text = f"{value:.2f}"
        return text

    # this is required when edit operation is called from QTableView
    def createEditor(self, aParent, option, index):
        float_editor = QLineEdit(aParent)
        float_editor.setValidator(QDoubleValidator(decimals=2))
        return float_editor

    def setEditorData(self, editor, index):
        amount = index.model().data(index, Qt.EditRole)
        if amount:
            editor.setText(self.formatFloatLong(float(amount)))
        else:
            QSqlRelationalDelegate.setEditorData(self, editor, index)

    def paint(self, painter, option, index):
        painter.save()
        amount = index.model().data(index, Qt.DisplayRole)
        text = ""
        if amount:
            text = self.formatFloatLong(float(amount))
        painter.drawText(option.rect, Qt.AlignRight, text)
        painter.restore()
