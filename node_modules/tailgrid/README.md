## 🚀 Quick Start

```typescriptreact
import { TailGrid } from 'tailgrid';
import 'tailgrid/dist/style.css';

const App = () => {
  const data = [
    { id: '1', name: 'John Doe', email: 'john@example.com', role: 'Developer' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com', role: 'Designer' },
    // ...more data
  ];

  const columns = [
    { key: 'name', header: 'Name', sortable: true },
    { key: 'email', header: 'Email', sortable: true },
    { key: 'role', header: 'Role', sortable: true },
  ];

  return (
    <TailGrid
      initialData={data}
      columns={columns}
      title="Team Members"
      subtitle="Manage your team members"
    />
  );
};
```

## 📚 Documentation

### Basic Usage

TailGrid is designed to be simple to use while offering extensive customization options:

```typescriptreact
<TailGrid
  initialData={data}
  columns={columns}
  title="Data Table"
  subtitle="Manage your data"
  pagination={true}
  sortable={true}
  hasFilterCapability={true}
/>
```

### Advanced Features

#### 1. Expandable Rows

```typescriptreact
<TailGrid
  initialData={data}
  columns={columns}
  expandableConfig={{
    enabled: true,
    renderExpandedContent: (row) => (
      <div>
        <h3>Additional Details</h3>
        <p>Created: {row.createdAt}</p>
        <p>Notes: {row.notes}</p>
      </div>
    ),
  }}
/>
```

#### 2. Custom Actions

```typescriptreact
<TailGrid
  initialData={data}
  columns={columns}
  actions={[
    {
      label: 'Edit',
      icon: 'pencil',
      onClick: (row) => handleEdit(row),
    },
    {
      label: 'Delete',
      icon: 'trash',
      onClick: (row) => handleDelete(row),
    },
  ]}
/>
```

#### 3. Server-Side Data Fetching

```typescriptreact
<TailGrid
  isServerSide={true}
  onDataFetch={async (page, pageSize) => {
    const response = await fetchData(page, pageSize);
    return {
      items: response.data,
      totalCount: response.meta.total,
      totalPages: response.meta.pages,
    };
  }}
  columns={columns}
/>
```

#### 4. Custom Filtering

```typescriptreact
<TailGrid
  initialData={data}
  columns={columns}
  filterFields={[
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'pending', label: 'Pending' },
      ],
    },
    {
      key: 'name',
      label: 'Name',
      type: 'text',
      placeholder: 'Search by name...',
    },
  ]}
/>
```

#### 5. Virtualization for Large Datasets

```typescriptreact
<TailGrid
  initialData={largeDataset}
  columns={columns}
  virtualized={true}
  rowHeight={56}
  maxHeight={600}
/>
```

### Styling and Theming

TailGrid is built with Tailwind CSS and can be easily customized:

```typescriptreact
<TailGrid
  initialData={data}
  columns={columns}
  containerClassName="my-custom-container"
  headerClassName="my-custom-header"
  bodyClassName="my-custom-body"
  rowClassName="my-custom-row"
  cellClassName="my-custom-cell"
/>
```

## 📋 Props Reference

### Core Props

| Prop | Type | Default | Description
|-----|-----|-----|-----
| `initialData` | `T[]` | `[]` | Array of data objects to display
| `columns` | `ColumnConfig<T>[]` | Required | Configuration for table columns
| `title` | `string` | - | Title displayed at the top of the component
| `subtitle` | `string` | - | Subtitle displayed below the title
| `rowKey` | `keyof T & string` | `'id'` | Key to use as row identifier


### Feature Props

| Prop | Type | Default | Description
|-----|-----|-----|-----
| `sortable` | `boolean` | `true` | Whether sorting is enabled
| `pagination` | `boolean` | `true` | Whether pagination is enabled
| `hasFilterCapability` | `boolean` | `true` | Whether filtering is enabled
| `filterFields` | `FilterField[]` | `[]` | Configuration for filter fields
| `actions` | `ActionConfig<T>[]` | `[]` | Array of action buttons to display
| `expandableConfig` | `ExpandableConfig<T>` | - | Configuration for expandable rows
| `virtualized` | `boolean` | `false` | Whether to use virtualization for large datasets
| `keyboardNavigation` | `boolean` | `true` | Whether to enable keyboard navigation
| `highlightOnHover` | `boolean` | `true` | Whether to highlight rows on hover
| `stickyHeader` | `boolean` | `true` | Whether to make the header sticky


### Server-Side Props

| Prop | Type | Default | Description
|-----|-----|-----|-----
| `isServerSide` | `boolean` | `false` | Whether to use server-side data fetching
| `onDataFetch` | `(page, pageSize) => Promise<DataFetchResponse<T>>` | - | Function for server-side data fetching
| `onServerFilter` | `(filters: FilterState[]) => Promise<void>` | - | Function for server-side filtering
| `onServerSort` | `(sort: SortState) => Promise<void>` | - | Function for server-side sorting
| `onServerSearch` | `(searchTerm: string) => Promise<void>` | - | Function for server-side search


### Styling Props

| Prop | Type | Default | Description
|-----|-----|-----|-----
| `containerClassName` | `string` | `''` | Custom class name for the container
| `headerClassName` | `string` | `''` | Custom class name for the header
| `bodyClassName` | `string` | `''` | Custom class name for the body
| `footerClassName` | `string` | `''` | Custom class name for the footer
| `rowClassName` | `string` | `''` | Custom class name for rows
| `cellClassName` | `string` | `''` | Custom class name for cells
| `headerCellClassName` | `string` | `''` | Custom class name for header cells


### Customization Props

| Prop | Type | Default | Description
|-----|-----|-----|-----
| `customFilterComponent` | `ReactNode` | - | Optional custom filter component
| `customLoadingComponent` | `ReactNode` | - | Option to customize the loading state
| `customNoDataComponent` | `ReactNode` | - | Option to customize the no data state
| `emptyStateMessage` | `string` | `'No data available'` | Message to display when there is no data
| `loadingMessage` | `string` | `'Loading data...'` | Message to display when loading data


## 🧩 Type Definitions

TailGrid is built with TypeScript and provides comprehensive type definitions:

```typescriptreact
// Basic usage with type safety
interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

<TailGrid<User>
  initialData={users}
  columns={[
    { key: 'name', header: 'Name', sortable: true },
    { key: 'email', header: 'Email', sortable: true },
    { key: 'role', header: 'Role', sortable: true },
  ]}
/>
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 💖 Support

If you find this project helpful, please consider supporting the developer:

<a href="https://ko-fi.com/ax3cubed" target="_blank">
  <img src="https://storage.ko-fi.com/cdn/kofi6.png?v=6" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

## 🙏 Acknowledgements

- [Tailwind CSS](https://tailwindcss.com/) - For the styling framework
- [shadcn/ui](https://ui.shadcn.com/) - For the UI components
- [Framer Motion](https://www.framer.com/motion/) - For the animations
- [Lucide Icons](https://lucide.dev/) - For the beautiful icons



