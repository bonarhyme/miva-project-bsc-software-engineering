import { ChevronLeft, ChevronRight, Trash } from "lucide-react";

import type { PageSize } from "../types";

type DataTableProps<T extends Record<string, unknown>> = {
  title: string;
  rows: T[];
  columns: string[];
  page: number;
  pageSize: PageSize;
  total: number;
  onAction?: (row: T) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: PageSize) => void;
};

function DataTable<T extends Record<string, unknown>>({
  title,
  rows,
  columns,
  page,
  pageSize,
  total,
  onAction,
  onPageChange,
  onPageSizeChange,
}: DataTableProps<T>) {
  const colSpan = columns.length + 1 + (onAction ? 1 : 0);
  const pageCount = pageSize === "all" ? 1 : Math.max(1, Math.ceil(total / pageSize));
  const start = total === 0 ? 0 : pageSize === "all" ? 1 : page * pageSize + 1;
  const end =
    total === 0
      ? 0
      : pageSize === "all"
        ? total
        : Math.min(total, (page + 1) * pageSize);

  return (
    <section className="table-wrap">
      <div className="table-header">
        <h2>{title}</h2>
        <label className="page-size-control">
          Show
          <select
            value={String(pageSize)}
            onChange={(event) => {
              const value = event.target.value;
              onPageSizeChange(value === "all" ? "all" : (Number(value) as PageSize));
            }}
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="all">All</option>
          </select>
        </label>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>S/N</th>
              {columns.map((column) => (
                <th key={column}>{column.replace("_", " ")}</th>
              ))}
              {onAction && <th>Action</th>}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={colSpan}>No records</td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr key={String(row.id || index)}>
                  <td>{start + index}</td>
                  {columns.map((column) => (
                    <td key={column}>{String(row[column] ?? "")}</td>
                  ))}
                  {onAction && (
                    <td>
                      <button
                        className="danger-button"
                        type="button"
                        title="Remove"
                        onClick={() => onAction(row)}
                      >
                        <Trash size={16} />
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="pagination-row">
        <span>
          {start}-{end} of {total}
        </span>
        <div>
          <button
            className="icon-button"
            type="button"
            title="Previous page"
            disabled={pageSize === "all" || page <= 0}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <span>
            Page {pageSize === "all" ? 1 : page + 1} of {pageCount}
          </span>
          <button
            className="icon-button"
            type="button"
            title="Next page"
            disabled={pageSize === "all" || page >= pageCount - 1}
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </section>
  );
}

export default DataTable;
